from sympy import linear_eq_to_matrix
from math import log2, floor, ceil

from msdsl.cpp import ap_fixed, ap_int, ap_uint
from msdsl.util import to_interval

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

class AnalogSignal:
    def __init__(self, name=None, range_=None, rel_tol=None, abs_tol=None, expr=None):
        # set defaults
        if range_ is None:
            range_ = [-1, 1]
        if (rel_tol is None) and (abs_tol is None):
            rel_tol = 5e-7

        # create interval if necessary
        range_ = to_interval(range_)

        # compute tolerance
        if rel_tol is not None:
            assert abs_tol is None, 'Cannot specify both relative and absolute tolerance.'
            abs_tol = rel_tol * max(abs(range_[0].inf), abs(range_[0].sup))

        # save settings
        self.name = name
        self.range_ = range_
        self.abs_tol = abs_tol
        self.expr = expr

    @property
    def rel_tol(self):
        if (self.range_[0].inf == 0) and (self.range_[0].sup == 0):
            return 0
        else:
            return self.abs_tol / max(abs(self.range_[0].inf), abs(self.range_[0].sup))

    def __add__(self, other):
        return AnalogSignal(range_=self.range_+other.range_, abs_tol=max(self.abs_tol, other.abs_tol))

    def __mul__(self, other):
        rel_tol = max(self.rel_tol, other.rel_tol)
        return AnalogSignal(range_ = self.range_*other.range_, rel_tol=rel_tol)

    @property
    def cpp_type(self):
        margin = 1.5

        if self.abs_tol == 0:
            assert (self.range_[0].inf == 0) and (self.range_[0].sup == 0), 'A tolerance of zero is only allowed for a value with range [0,0]'
            return ap_fixed(1, 1)

        lsb = floor(log2(self.abs_tol))
        width = max(signed_int_width(margin*self.range_[0].inf/(2**lsb)),
                    signed_int_width(margin*self.range_[0].sup/(2**lsb)))

        return ap_fixed(width, width+lsb)


class DigitalSignal:
    def __init__(self, name=None, signed=False, width=1, expr=None):
        self.name = name
        self.signed = signed
        self.width = width
        self.expr = expr

    def __str__(self):
        return self.name

    @property
    def cpp_type(self):
        if self.signed:
            return ap_int(self.width)
        else:
            return ap_uint(self.width)


class CaseLinearExpr:
    def __init__(self, num_cases, coeffs=None, const=None):
        # set defaults
        if coeffs is None:
            coeffs = {}
        if const is None:
            const = [0] * num_cases

        self.num_cases = num_cases
        self.coeffs = coeffs
        self.const = const

    def add_case(self, case_no, expr):
        syms = list(expr.free_symbols)
        sym_names = [sym.name for sym in syms]

        A, b = linear_eq_to_matrix([expr], syms)

        # add variables
        vars = [float(x) for x in A]
        for sym_name, var in zip(sym_names, vars):
            if sym_name not in self.coeffs:
                self.coeffs[sym_name] = [0] * self.num_cases
            self.coeffs[sym_name][case_no] = var

        # add constant
        self.const[case_no] = -float(b[0])


class MixedSignalModel:
    def __init__(self, mode=None, analog_inputs=None, digital_inputs=None, analog_outputs=None, analog_states=None,
                 digital_states=None):

        self.mode = mode
        self.analog_inputs = analog_inputs if analog_inputs is not None else []
        self.digital_inputs = digital_inputs if digital_inputs is not None else []
        self.analog_outputs = analog_outputs if analog_outputs is not None else []
        self.analog_states = analog_states if analog_states is not None else []
        self.digital_states = digital_states if digital_states is not None else []