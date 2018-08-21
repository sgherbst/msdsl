import sys
import argparse

from math import log2, floor, ceil
from interval import interval

from msdsl.format import load_model
from msdsl.util import Namespace
from msdsl.model import AnalogSignal, CaseLinearExpr
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
            # get the coefficients from cases that were actually defined
            coeffs_present = [prod.coeffs[k] for k in expr.cases_present]

            # check if all zeros
            if all(coeff_val==0 for coeff_val in coeffs_present):
                continue

            # create a constant or array as necessary
            const_val = coeffs_present[0]
            if all(coeff_val==const_val for coeff_val in coeffs_present):
                if (const_val == 1) and (prod.var is not None):
                    # special case: if the coefficients are all "1", then no multiplication is necessary
                    terms.append(prod.var)
                    continue
                else:
                    term = instance(self.type_(self.val_to_signal(const_val)), const_val)
            else:
                arr = self.namespace.make(prefix='arr')
                self.cpp_gen.array(self.type_(self.arr_to_signal(prod.coeffs)), arr, prod.coeffs)

                term = arr + '[idx]'

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
        return ptr(self.expr_type(output.expr, rel_tol=output.rel_tol, abs_tol=output.abs_tol))

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
        elif len(expr.children) == 1:
            child = DigitalFormatter.expr2str(expr.children[0])
            return expr.data + '(' + child + ')'
        elif len(expr.children) == 2:
            child_1 = DigitalFormatter.expr2str(expr.children[0])
            child_2 = DigitalFormatter.expr2str(expr.children[1])
            return '(' + child_1 + ')' + expr.data + '(' + child_2 + ')'


def main():
    parser = argparse.ArgumentParser(description='Generate C++ code from mixed-signal intermediate representation.')
    parser.add_argument('-i', type=str, help='Input file.', default='../build/circuit.json')
    parser.add_argument('-o', type=str, help='Output file.', default='../build/circuit.cpp')
    parser.add_argument('--use_float', action='store_true', help='Use floating-point numbers (instead of fixed-point)')

    args = parser.parse_args()

    file_text = open(args.i, 'r').read()
    model = load_model(file_text)

    cpp_gen = CppGen(filename=args.o)
    namespace = Namespace()

    analog_fmt = AnalogFormatter(use_float=args.use_float, cpp_gen=cpp_gen, namespace=namespace, model=model)
    digital_fmt = DigitalFormatter()

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    # macros
    if args.use_float:
        cpp_gen.define('SIGN_BIT(x)', 'ap_uint<1>(((x) < 0) ? 1 : 0)')
    else:
        cpp_gen.define('SIGN_BIT(x)', '(ap_uint<1>(x[x.length()-1]))')
    cpp_gen.print()

    # start function representing circuit
    io = []
    io += [(analog_fmt.type_(analog_input), analog_input.name) for analog_input in model.analog_inputs]
    io += [(digital_fmt.type_(digital_input), digital_input.name) for digital_input in model.digital_inputs]
    io += [(analog_fmt.output_format(analog_output), analog_output.name) for analog_output in model.analog_outputs]
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

    # create the case index variable
    cpp_gen.comment('Case index variable')
    cpp_gen.assign(ap_uint(len(model.mode)) + ' ' + 'idx', concat(*model.mode))
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

    # update digital states into temporary variables
    tmpvars = []
    for digital_state in model.digital_states:
        cpp_gen.comment('Update digital state: ' + digital_state.name)

        for expr in digital_state.expr.walk():
            if isinstance(expr.data, CaseLinearExpr):
                tmpvar = namespace.make(prefix='tmp')
                cpp_gen.assign(analog_fmt.expr_type(expr.data) + ' ' + tmpvar, analog_fmt.make_expr(expr.data))
                expr.data = 'SIGN_BIT(' + tmpvar + ')'

        tmpvar = namespace.make(prefix='tmp')
        tmpvars.append((digital_state.name, tmpvar))
        cpp_gen.assign(digital_fmt.type_(digital_state) + ' ' + tmpvar, digital_fmt.expr2str(digital_state.expr))
        cpp_gen.print()

    # update digital states from temporary variables
    cpp_gen.comment('Assigning digital states from temporary variables')
    for state, tmpvar in tmpvars:
        cpp_gen.assign(state, tmpvar)
    cpp_gen.print()

    cpp_gen.end_function()

if __name__ == '__main__':
    main()