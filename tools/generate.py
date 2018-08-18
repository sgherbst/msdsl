import sys

from msdsl.format import load_model
from msdsl.util import Namespace
from msdsl.cpp import *
from msdsl.model import AnalogSignal

def arr_to_signal(arr):
    return AnalogSignal(range_=[min(arr), max(arr)])

def decl_arrays(f, namespace, expr):
    prods = [(namespace.make(prefix='arr'), key) for key in expr.coeffs.keys()]
    for coeff, var in prods:
        f.array(arr_to_signal(expr.coeffs[var]).cpp_type, coeff, expr.coeffs[var])

    offset = namespace.make(prefix='arr')
    f.array(arr_to_signal(expr.const).cpp_type, offset, expr.const)

    return prods, offset

def linexpr(prods=None, offset=None):
    if prods is None:
        prods = []

    terms = []
    terms.extend([coeff + '[idx]*' + var for coeff, var in prods])

    if offset is not None:
        terms.append(offset + '[idx]')

    return ' + '.join(terms)

def expr_format(model, expr):
    signals = {signal.name: signal for signal in (model.analog_inputs+model.analog_states)}

    fmt = arr_to_signal(expr.const)

    for signal_name, coeffs in expr.coeffs.items():
        fmt += arr_to_signal(coeffs) * signals[signal_name]

    return fmt

def main():
    if len(sys.argv) >= 2:
        file_name = sys.argv[1]
    else:
        file_name = '../build/circuit.json'

    file_text = open(file_name, 'r').read()
    model = load_model(file_text)

    f = CppGen()
    namespace = Namespace()

    # include files
    f.include('"ap_int.h"')
    f.include('"ap_fixed.h"')
    f.print()

    # start function representing circuit
    io = []
    io += [(analog_input.cpp_type, analog_input.name) for analog_input in model.analog_inputs]
    io += [(digital_input.cpp_type, digital_input.name) for digital_input in model.digital_inputs]
    io += [(ptr(expr_format(model, analog_output.expr).cpp_type), analog_output.name)
           for analog_output in model.analog_outputs]
    f.start_function('void', 'circuit', io)

    # declare analog state variables
    f.comment('Analog state variables')
    for analog_state in model.analog_states:
        f.static(analog_state.cpp_type, analog_state.name)
    f.print()

    # declare digital state variables
    f.comment('Digital state variables')
    for digital_state in model.digital_states:
        f.static(digital_state.cpp_type, digital_state.name)
    f.print()

    # create the case index variable
    f.comment('Case index variable')
    f.assign(ap_uint(len(model.mode)) + ' ' + 'idx', concat(*model.mode))
    f.print()

    # update digital states
    for digital_state in model.digital_states:
        f.comment('Update digital state: ' + digital_state.name)
        prods, offset = decl_arrays(f, namespace, digital_state.expr)
        f.assign(digital_state.name, gt(parens(linexpr(prods, offset)),
                                        instance(expr_format(model, digital_state.expr).cpp_type, 0.0)))
        f.print()

    # update analog states
    for analog_state in model.analog_states:
        f.comment('Update analog state: ' + analog_state.name)
        prods, offset = decl_arrays(f, namespace, analog_state.expr)
        f.assign(analog_state.name, linexpr(prods, offset))
        f.print()

    # print the outputs
    for analog_output in model.analog_outputs:
        f.comment('Calculate analog output: ' + analog_output.name)
        prods, offset = decl_arrays(f, namespace, analog_output.expr)
        f.assign(deref(analog_output.name), linexpr(prods, offset))
        f.print()

    f.end_function()

if __name__ == '__main__':
    main()