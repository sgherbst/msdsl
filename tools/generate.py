import sys
from msdsl.util import from_json
from msdsl.util import Namespace
from msdsl.cpp import *

def decl_arrays(f, namespace, expr):
    prods = [(namespace.make('arr'), key) for key in expr['coeffs'].keys()]
    for coeff, var in prods:
        f.array(const('coeff'), coeff, expr['coeffs'][var])

    offset = namespace.make('arr')
    f.array('real', offset, expr['offset'])

    return prods, offset


def linexpr(prods=None, offset=None):
    if prods is None:
        prods = []

    terms = []
    terms.extend([coeff + '[idx]*' + var for coeff, var in prods])

    if offset is not None:
        terms.append(offset + '[idx]')

    return ' + '.join(terms)


def main():
    if len(sys.argv) >= 2:
        file_name = sys.argv[1]
    else:
        file_name = '../build/circuit.json'

    file_text = open(file_name, 'r').read()
    circuit = from_json(file_text)

    f = CppGen()
    namespace = Namespace()

    # include files
    f.include('"ap_int.h"')
    f.include('"ap_fixed.h"')
    f.print()

    # start function representing circuit
    io = []
    io += [('real', analog_input) for analog_input in circuit['analog_inputs']]
    io += [('bit', digital_input) for digital_input in circuit['digital_inputs']]
    io += [(ptr('real'), output) for output in circuit['analog_outputs'].keys()]
    f.start_function('void', 'circuit', io)

    # declare analog state variables
    f.comment('Analog state variables')
    for state, params in circuit['analog_states'].items():
        f.static('real', state)
    f.print()

    # declare digital state variables
    f.comment('Digital state variables')
    for state, params in circuit['digital_states'].items():
        f.static('bit', state)
    f.print()

    # create the case index variable
    f.comment('Case index variable')
    f.assign(ap_uint(len(circuit['idx'])) + ' ' + 'idx', concat(*circuit['idx']))
    f.print()

    # update digital states
    for state, expr in circuit['digital_states'].items():
        f.comment('Update digital state: ' + state)
        prods, offset = decl_arrays(f, namespace, expr)
        f.assign(state, gt(parens(linexpr(prods, offset)), instance('real', 0.0)))
        f.print()

    # update analog states
    for state, expr in circuit['analog_states'].items():
        f.comment('Update analog state: ' + state)
        prods, offset = decl_arrays(f, namespace, expr)
        f.assign(state, linexpr(prods, offset))
        f.print()

    # print the outputs
    for output, expr in circuit['analog_outputs'].items():
        f.comment('Calculate analog output: ' + output)
        prods, offset = decl_arrays(f, namespace, expr)
        f.assign(deref(output), linexpr(prods, offset))
        f.print()

    f.end_function()

if __name__ == '__main__':
    main()