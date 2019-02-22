from numbers import Integral
from msdsl.expr import Case, DigitalSignal, ListOp, BinaryOp, AnalogConstant

def addr2settings(addr, sel_bits):
    assert isinstance(addr, Integral) and (0 <= addr) and (addr <= ((1 << len(sel_bits)) - 1))

    sel_bit_settings = {}

    for idx, sel_bit in enumerate(sel_bits[::-1]):
        sel_bit_settings[sel_bit.name] = (addr >> idx) & 1

    return sel_bit_settings

def subst_case(expr, sel_bit_settings):
    if not

    if isinstance(expr, Case):
        return AnalogConstant(expr.settings2term(sel_bit_settings))
    if isinstance(expr, ListOp):
        return type(expr)(subst_case(term, sel_bit_settings) for term in expr.terms)
    elif isinstance(expr, BinaryOp):
        return type(expr)(subst_case(expr.lhs, sel_bit_settings), subst_case(expr.rhs, sel_bit_settings))
    else:
        return expr

class EqnCase(ModelExpr):
    def __init__(self, terms, sel_bits):
        self.terms = terms
        self.sel_bits = sel_bits

    def settings2term(self, sel_bit_settings):
        return self.terms[self.settings2addr(sel_bit_settings)]

    def settings2addr(self, sel_bit_settings):
        bit_str = ''.join([str(sel_bit_settings[sel_bit.name]) for sel_bit in self.sel_bits])
        return int(bit_str, 2)

def main():
    a = DigitalSignal('a')
    b = DigitalSignal('b')
    c = DigitalSignal('c')

    sel_bits = [a, b, c]
    sel_bit_settings = addr2settings(0, sel_bits)
    print(sel_bit_settings)

    case = Case(['a', 'b', 'c', 'd'], [c, a])
    print(case.settings2term(sel_bit_settings))

if __name__ == '__main__':
    main()