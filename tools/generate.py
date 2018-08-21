import sys

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
            return 'double'

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

    def decl_arrays(self, expr):
        prods = []

        for prod in expr.prods:
            # declare the array
            coeff_array_name = self.namespace.make(prefix='arr')
            coeff_array_type = self.type_(self.arr_to_signal(prod.coeffs))
            self.cpp_gen.array(coeff_array_type, coeff_array_name, prod.coeffs)

            # save the pair of coefficient array and variable names
            prods.append((coeff_array_name, prod.var))

        # declare the array of constants
        offset_array_name = self.namespace.make(prefix='arr')
        offset_array_type = self.type_(self.arr_to_signal(expr.const.coeffs))
        self.cpp_gen.array(offset_array_type, offset_array_name, expr.const.coeffs)

        return prods, offset_array_name

    def arr_to_signal(self, arr):
        return AnalogSignal(range_=[min(arr), max(arr)], rel_tol=self.coeff_rel_tol)

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

def linexpr(prods, const):
    terms = [coeff + '[idx]*' + var for coeff, var in prods]

    if const is not None:
        terms.append(const + '[idx]')

    return ' + '.join(terms)

def main():
    if len(sys.argv) >= 2:
        file_name = sys.argv[1]
    else:
        file_name = '../build/circuit.json'

    file_text = open(file_name, 'r').read()
    model = load_model(file_text)
    print(model)

    cpp_gen = CppGen()
    namespace = Namespace()

    analog_fmt = AnalogFormatter(cpp_gen=cpp_gen, namespace=namespace, model=model)
    digital_fmt = DigitalFormatter()

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    # macros
    cpp_gen.print('#define SIGN_BIT(x) (ap_uint<1>(x[x.length()-1]))')
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

    # update digital states
    for digital_state in model.digital_states:
        for expr in digital_state.expr.walk():
            if isinstance(expr.data, CaseLinearExpr):
                cpp_gen.comment('Making temporary variable')
                tmpvar = namespace.make(prefix='tmp')
                prods, offset = analog_fmt.decl_arrays(expr.data)
                cpp_gen.assign(analog_fmt.expr_type(expr.data) + ' ' + tmpvar, linexpr(prods, offset))
                cpp_gen.print()
                expr.data = 'SIGN_BIT(' + tmpvar + ')'
        cpp_gen.comment('Update digital state: ' + digital_state.name)
        cpp_gen.assign(digital_state.name, digital_fmt.expr2str(digital_state.expr))
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
        prods, offset = analog_fmt.decl_arrays(analog_state.expr)
        cpp_gen.assign(analog_fmt.type_(analog_state) + ' ' + tmpvar, linexpr(prods, offset))
        cpp_gen.print()

    # update analog states from temporary variables
    cpp_gen.comment('Assigning analog states from temporary variables')
    for state, tmpvar in tmpvars:
        cpp_gen.assign(state, tmpvar)
    cpp_gen.print()

    # print the outputs
    for analog_output in model.analog_outputs:
        cpp_gen.comment('Calculate analog output: ' + analog_output.name)
        prods, offset = analog_fmt.decl_arrays(analog_output.expr)
        cpp_gen.assign(deref(analog_output.name), linexpr(prods, offset))
        cpp_gen.print()

    cpp_gen.end_function()

if __name__ == '__main__':
    main()