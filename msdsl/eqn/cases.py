from numbers import Integral
from typing import List

from msdsl.expr.format import RealFormat, UIntFormat
from msdsl.expr.expr import wrap_constants, promote_operands, EqualTo, Sum, Product, prod_op, sum_op, ModelExpr
from msdsl.expr.signals import DigitalSignal, Signal
from msdsl.expr.svreal import UndefinedRange

def subst_case(expr, sel_bit_settings):
    if isinstance(expr, EqnCase):
        # select the appropriate case
        case = expr.get_case(sel_bit_settings)

        # apply case substitution again (allows for nested cases)
        case = subst_case(case, sel_bit_settings)

        # return result
        return case
    elif isinstance(expr, EqualTo):
        return EqualTo(subst_case(expr.lhs, sel_bit_settings), subst_case(expr.rhs, sel_bit_settings))
    elif isinstance(expr, Sum):
        return sum_op(subst_case(operand, sel_bit_settings) for operand in expr.operands)
    elif isinstance(expr, Product):
        return prod_op(subst_case(operand, sel_bit_settings) for operand in expr.operands)
    else:
        return expr

def address_to_settings(address, sel_bits):
    # sanity checks
    assert isinstance(address, Integral), 'Address must be an integer.'
    assert 0 <= address <= (1 << len(sel_bits)) - 1, f'The address {address} cannot be represented using {len(sel_bits)} sel_bits.'

    # build up the dictionary of settings
    sel_bit_settings = {}
    for idx, sel_bit in enumerate(sel_bits[::-1]):
        sel_bit_settings[sel_bit.name] = (address >> idx) & 1

    # return the settings
    return sel_bit_settings

def eqn_case(cases, sel_bits: List[DigitalSignal]):
    """
    Add a EqnCase object to a MixedSignalModel object of MSDSL. The EqnCase object was populated by cases and sel_bits
    that were provided to this function.

    :param cases:       equations for each case that is part of the case statement.
    :param sel_bits:    list of bits that is used to evaluate the case statement.
    :return:            EqnCase object
    """
    # wrap constants and promote them to RealFormat
    cases = wrap_constants(cases)
    cases = promote_operands(cases, RealFormat)

    # sanity check
    assert all(isinstance(sel_bit, Signal) and isinstance(sel_bit.format_, UIntFormat) and sel_bit.format_.width == 1
               for sel_bit in sel_bits), 'Selection bits for an EqnCase must all be 1-bit unsigned digital signals.'
    assert len(cases) == (1<<len(sel_bits)), 'Case table length must match 2**len(sel_bits).'

    # return the result
    if len(cases) == 0:
        raise ValueError('EqnCase must have at least one case.')
    elif len(cases) == 1:
        return cases[0]
    else:
        return EqnCase(cases=cases, sel_bits=sel_bits)

class EqnCase(ModelExpr):
    def __init__(self, cases, sel_bits):
        # save settings
        self.cases = cases
        self.sel_bits = sel_bits

        # call the super constructor
        super().__init__(format_=RealFormat(range_=UndefinedRange()))

    def get_address(self, sel_bit_settings):
        # returns the case table address corresponding to the given sel_bit_settings.  note that some sel_bits
        # in sel_bit_settings may not be present in this EqnCase.  that's OK; they are effectively treated
        # as don't care bits and do not consume extra resources.
        addr = 0
        for sel_bit in self.sel_bits:
            addr <<= 1
            addr |= 1 if sel_bit_settings[sel_bit.name] else 0
        return addr

    def get_case(self, sel_bit_settings):
        # returns the expression corresponsing
        return self.cases[self.get_address(sel_bit_settings)]

    def __str__(self):
        cases = '[' + ', '.join(str(case) for case in self.cases) + ']'
        sel_bits = '{' + ', '.join(str(sel_bit) for sel_bit in self.sel_bits) + '}'
        return f'EqnCase({cases}, {sel_bits})'

def main():
    a = DigitalSignal('a')
    b = DigitalSignal('b')
    c = DigitalSignal('c')

    sel_bits = [a, b, c]
    print(address_to_settings(0, sel_bits))
    print(address_to_settings(1, sel_bits))
    print(address_to_settings(2, sel_bits))
    print(address_to_settings(3, sel_bits))
    print(address_to_settings(4, sel_bits))
    print(address_to_settings(5, sel_bits))
    print(address_to_settings(6, sel_bits))
    print(address_to_settings(7, sel_bits))

    expr = 1 + eqn_case([-1, 1], [a])
    print(expr, expr.format_.range_)

    expr = subst_case(expr, {'a': 1})
    print(expr, expr.format_.range_)

if __name__ == '__main__':
    main()