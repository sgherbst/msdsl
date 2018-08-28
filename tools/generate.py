import argparse

from math import log2, floor, ceil
from interval import interval

from msdsl.format import load_model
from msdsl.util import Namespace
from msdsl.model import AnalogSignal, CaseLinearExpr, DigitalSignal
from msdsl.cpp import *

class AnalogFormatter:
    def __init__(self, cpp_gen, namespace, model, use_float=False, range_margin=1.5, coeff_rel_tol=5e-5):
        self.cpp_gen = cpp_gen
        self.namespace = namespace
        self.model = model
        self.use_float = use_float
        self.range_margin = range_margin
        self.coeff_rel_tol = coeff_rel_tol

    def type_(self, signal):
        # handle case where floating point numbers are used
        if self.use_float:
            return 'float'

        # compute absolute tolerance if needed
        if signal.abs_tol is None:
            abs_tol = max(abs(signal.range_[0]), abs(signal.range_[1])) * signal.rel_tol
        else:
            abs_tol = signal.abs_tol

        # handle case that tolerance is zero
        if abs_tol == 0:
            assert (signal.range_[0] == 0) and (signal.range_[1] == 0)
            return ap_fixed(1, 1)

        # compute fixed point format
        lsb = floor(log2(abs_tol))
        width = max(self.signed_int_width(self.range_margin * signal.range_[0] / (2 ** lsb)),
                    self.signed_int_width(self.range_margin * signal.range_[1] / (2 ** lsb)))

        return ap_fixed(width, width + lsb)

    def arr_to_signal(self, arr):
        return AnalogSignal(range_=[min(arr), max(arr)], rel_tol=self.coeff_rel_tol)

    def val_to_signal(self, val):
        return self.arr_to_signal([val, val])

    def make_expr(self, expr):
        terms = []
        for prod in (expr.prods + [expr.const]):
            # check if all zeros
            if all(coeff_val==0 for coeff_val in prod.coeffs):
                continue

            # create a constant or array as necessary
            const_val = prod.coeffs[0]
            if all(coeff_val==const_val for coeff_val in prod.coeffs):
                if (const_val == 1) and (prod.var is not None):
                    # special case: if the coefficients are all "1", then no multiplication is necessary
                    terms.append(prod.var)
                    continue
                else:
                    term = instance(self.type_(self.val_to_signal(const_val)), const_val)
            else:
                arr = self.namespace.make(prefix='arr')
                self.cpp_gen.array(self.type_(self.arr_to_signal(prod.coeffs)), arr, prod.coeffs)

                term = arr + '[' + expr.mode + ']'

            # multiply by variable if defined
            if prod.var is not None:
                term += '*' + prod.var

            # add to terms list
            terms.append(term)

        return ' + '.join(terms)

    def expr_type(self, expr, rel_tol=None, abs_tol=None):
        range_ = interval[min(expr.const.coeffs), max(expr.const.coeffs)]

        for prod in expr.prods:
            coeff_range = interval[min(prod.coeffs), max(prod.coeffs)]
            var_range = interval(self.model.get_signal(prod.var).range_)
            range_ += (coeff_range * var_range)

        range_ = [range_[0].inf, range_[0].sup]

        return self.type_(AnalogSignal(range_=range_, rel_tol=rel_tol, abs_tol=abs_tol))

    def output_format(self, output):
        return self.expr_type(output.expr, rel_tol=output.rel_tol, abs_tol=output.abs_tol)

    @staticmethod
    def signed_int_width(int_val):
        """Returns the number of bits required to represent int_val as a signed integer.  If int_val is zero,
        the number of bits required is defined to be one.
        """

        if int_val < 0:
            return ceil(log2(-int_val) + 1)
        elif int_val > 0:
            return ceil(log2(int_val + 1) + 1)
        else:
            return 1


class DigitalFormatter:
    def __init__(self, model):
        self.model = model

    @staticmethod
    def type_(signal):
        if signal.signed:
            return ap_int(signal.width)
        else:
            return ap_uint(signal.width)

    @staticmethod
    def expr2str(expr):
        if len(expr.children) == 0:
            return expr.data
        else:
            if expr.data == 'concat':
                return '(' + ', '.join(DigitalFormatter.expr2str(child) for child in expr.children) + ')'
            elif expr.data == '~':
                return expr.data + '(' + DigitalFormatter.expr2str(expr.children[0]) + ')'
            elif expr.data in ['&', '|']:
                child_0 = DigitalFormatter.expr2str(expr.children[0])
                child_1 = DigitalFormatter.expr2str(expr.children[1])
                return '(' + child_0 + ')' + expr.data + '(' + child_1 + ')'
            else:
                raise ValueError('Invalid digital expression type.')

def make_header(args, model):
    cpp_gen = CppGen(filename=args.hpp)
    namespace = Namespace()

    analog_fmt = AnalogFormatter(use_float=args.use_float, cpp_gen=cpp_gen, namespace=namespace, model=model)
    digital_fmt = DigitalFormatter(model=model)

    # start include guard
    include_guard_var = '__' + args.hpp.upper().replace('.', '_') + '__'
    cpp_gen.start_include_guard(include_guard_var)
    cpp_gen.print()

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    # macro(s)
    macro_name = 'LESS_THAN_ZERO(x)'
    if args.use_float:
        cpp_gen.define(macro_name, 'ap_uint<1>(((x) < 0) ? 1 : 0)')
    else:
        cpp_gen.define(macro_name, '(ap_uint<1>(x[x.length()-1]))')
    cpp_gen.print()

    # declare I/O types
    io = []

    cpp_gen.comment('analog inputs')
    for analog_input in model.analog_inputs:
        type_ = analog_fmt.type_(analog_input)
        type_name = analog_input.name + '_type'
        cpp_gen.typedef(type_, type_name)
        io.append((type_name, analog_input.name))
    cpp_gen.print()

    cpp_gen.comment('digital inputs')
    for digital_input in model.digital_inputs:
        type_ = digital_fmt.type_(digital_input)
        type_name = digital_input.name + '_type'
        cpp_gen.typedef(type_, type_name)
        io.append((type_name, digital_input.name))
    cpp_gen.print()

    cpp_gen.comment('analog outputs')
    for analog_output in model.analog_outputs:
        type_ = analog_fmt.output_format(analog_output)
        type_name = analog_output.name + '_type'
        cpp_gen.typedef(type_, type_name)
        io.append((ptr(type_name), analog_output.name))
    cpp_gen.print()

    # declare function prototype
    cpp_gen.comment('function prototype')
    cpp_gen.function_prototype('void', 'circuit', io)
    cpp_gen.print()

    # end include guard
    cpp_gen.end_include_guard(include_guard_var)

def make_source(args, model):
    cpp_gen = CppGen(filename=args.cpp)
    namespace = Namespace()

    analog_fmt = AnalogFormatter(use_float=args.use_float, cpp_gen=cpp_gen, namespace=namespace, model=model)
    digital_fmt = DigitalFormatter(model=model)

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    cpp_gen.include('"' + args.hpp + '"')
    cpp_gen.print()

    # start function representing circuit
    io = []
    io += [(analog_input.name + '_type', analog_input.name) for analog_input in model.analog_inputs]
    io += [(digital_input.name + '_type', digital_input.name) for digital_input in model.digital_inputs]
    io += [(ptr(analog_output.name + '_type'), analog_output.name) for analog_output in model.analog_outputs]
    cpp_gen.start_function('void', 'circuit', io)

    # declare analog state variables
    cpp_gen.comment('Analog state variables')
    for analog_state in model.analog_states:
        cpp_gen.static(analog_fmt.type_(analog_state), analog_state.name, initial=analog_state.initial)
    cpp_gen.print()

    # declare digital state variables
    cpp_gen.comment('Digital state variables')
    for digital_state in model.digital_states:
        cpp_gen.static(digital_fmt.type_(digital_state), digital_state.name, initial=digital_state.initial)
    cpp_gen.print()

    # create the digital mode variables
    for mode in model.digital_modes:
        if len(mode.expr.children) > 0:
            cpp_gen.comment('Digital mode variable: ' + mode.name)
            cpp_gen.assign(digital_fmt.type_(mode) + ' ' + mode.name, digital_fmt.expr2str(mode.expr))
            cpp_gen.print()

    # update digital states into temporary variables
    tmpvars = []
    for digital_state in model.digital_states:
        cpp_gen.comment('Update digital state: ' + digital_state.name)

        for expr in digital_state.expr.walk():
            if isinstance(expr.data, CaseLinearExpr):
                tmpvar = namespace.make(prefix='tmp')
                cpp_gen.assign(analog_fmt.expr_type(expr.data) + ' ' + tmpvar, analog_fmt.make_expr(expr.data))
                expr.data = 'LESS_THAN_ZERO(' + tmpvar + ')'

        tmpvar = namespace.make(prefix='tmp')
        tmpvars.append((digital_state.name, tmpvar))
        cpp_gen.assign(digital_fmt.type_(digital_state) + ' ' + tmpvar, digital_fmt.expr2str(digital_state.expr))
        cpp_gen.print()

    # update digital states from temporary variables
    cpp_gen.comment('Assigning digital states from temporary variables')
    for state, tmpvar in tmpvars:
        cpp_gen.assign(state, tmpvar)
    cpp_gen.print()

    # create the digital mode variables
    for mode in model.analog_modes:
        if len(mode.expr.children) > 0:
            cpp_gen.comment('Analog mode variable: ' + mode.name)
            cpp_gen.assign(digital_fmt.type_(mode) + ' ' + mode.name, digital_fmt.expr2str(mode.expr))
            cpp_gen.print()

    # update analog states into temporary variables
    tmpvars = []
    for analog_state in model.analog_states:
        # make temporary variable
        tmpvar = namespace.make(prefix='tmp')
        tmpvars.append((analog_state.name, tmpvar))

        # assign to temporary variable
        cpp_gen.comment('Update analog state: ' + analog_state.name)
        cpp_gen.assign(analog_fmt.type_(analog_state) + ' ' + tmpvar, analog_fmt.make_expr(analog_state.expr))
        cpp_gen.print()

    # update analog states from temporary variables
    cpp_gen.comment('Assigning analog states from temporary variables')
    for state, tmpvar in tmpvars:
        cpp_gen.assign(state, tmpvar)
    cpp_gen.print()

    # update the outputs
    for analog_output in model.analog_outputs:
        cpp_gen.comment('Calculate analog output: ' + analog_output.name)
        cpp_gen.assign(deref(analog_output.name), analog_fmt.make_expr(analog_output.expr))
        cpp_gen.print()

    cpp_gen.end_function()

def main():
    parser = argparse.ArgumentParser(description='Generate C++ code from mixed-signal intermediate representation.')
    parser.add_argument('--json', type=str, help='Input JSON file.', default='circuit.json')
    parser.add_argument('--cpp', type=str, help='Output C++ source file.', default='circuit.cpp')
    parser.add_argument('--hpp', type=str, help='Output C++ header file.', default='circuit.hpp')
    parser.add_argument('--use_float', action='store_true', help='Use floating-point numbers (instead of fixed-point)')

    args = parser.parse_args()

    file_text = open(args.json, 'r').read()
    model = load_model(file_text)

    # make the header
    make_header(args=args, model=model)

    # make the source code
    make_source(args=args, model=model)

if __name__ == '__main__':
    main()