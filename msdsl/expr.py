from typing import List
from numbers import Number, Integral

class ModelExpr:
    # addition and multiplication

    def handle_arith(self, other, op_cls):
        if isinstance(other, Number):
            other = Constant(other)

        if isinstance(other, ModelExpr):
            return op_cls([self, other])
        else:
            raise NotImplementedError

    def __add__(self, other):
        return self.handle_arith(other, Plus)

    def __mul__(self, other):
        return self.handle_arith(other, Times)

    # other arithmetic operations

    def __sub__(self, other):
        return self.__add__(-other)

    def __neg__(self):
        return -1.0*self

    def __truediv__(self, other):
        return (1.0/other)*self

    # reverse arithmetic operations

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rsub__(self, other):
        return (-self).__add__(other)

    # binary operations

    def __invert__(self):
        return BitwiseInv(self)

    def __and__(self, other):
        return BitwiseAnd(self, other)

    def __or__(self, other):
        return BitwiseOr(self, other)

    def __xor__(self, other):
        return BitwiseXor(self, other)

    # comparisons

    def handle_comp(self, other, op_cls):
        if isinstance(other, Number):
            other = Constant(other)

        return op_cls(self, other)

    def __le__(self, other):
        return self.handle_comp(other, LessThanOrEquals)

    def __lt__(self, other):
        return self.handle_comp(other, LessThan)

    def __ge__(self, other):
        return self.handle_comp(other, GreaterThanOrEquals)

    def __gt__(self, other):
        return self.handle_comp(other, GreaterThan)

    def __eq__(self, other):
        return self.handle_comp(other, EqualTo)

    def __ne__(self, other):
        return self.handle_comp(other, NotEqualTo)

    def __pos__(self):
        return self

class Constant(ModelExpr):
    def __init__(self, value: Number):
        self.value = value

    def __str__(self):
        return str(self.value)

class DigitalConstant(ModelExpr):
    def __init__(self, value: Integral, width: Integral = 1, signed: bool = False):
        self.value = value
        self.width = width
        self.signed = signed

    def __str__(self):
        sign_str = '-' if self.value < 0 else ''
        is_signed_str = 's' if self.signed else ''
        return str(f"{sign_str}{self.width}'{is_signed_str}d{abs(self.value)}")

class Deriv(ModelExpr):
    def __init__(self, expr: ModelExpr):
        self.expr = expr

    def __str__(self):
        return 'D(' + str(self.expr) + ')'

class ListOp(ModelExpr):
    def __init__(self, terms: List[ModelExpr]):
        self.terms = list(terms)

    @staticmethod
    def func(terms):
        raise NotImplementedError

    @property
    def identity(self):
        raise NotImplementedError

class Plus(ListOp):
    @staticmethod
    def func(terms):
        return sum(terms)

    @property
    def identity(self):
        return 0

    def __str__(self):
        return '(' + '+'.join(str(term) for term in self.terms) + ')'

class Times(ListOp):
    @staticmethod
    def func(terms):
        retval = 1
        for term in terms:
            retval *= term
        return retval

    @property
    def identity(self):
        return 1

    def __str__(self):
        return '(' + '*'.join(str(term) for term in self.terms) + ')'

class Min(ListOp):
    @staticmethod
    def func(terms):
        return min(*terms)

    @property
    def identity(self):
        return +float('inf')

    def __str__(self):
        return 'min(' + ', '.join(str(term) for term in self.terms) + ')'

class Max(ListOp):
    @staticmethod
    def func(terms):
        return max(*terms)

    @property
    def identity(self):
        return -float('inf')

    def __str__(self):
        return 'max(' + ', '.join(str(term) for term in self.terms) + ')'

class UnaryOp(ModelExpr):
    def __init__(self, term):
        self.term = term

class BitwiseInv(UnaryOp):
    def __str__(self):
        return f'(~{self.term})'

class BinaryOp(ModelExpr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class BitwiseAnd(BinaryOp):
    def __str__(self):
        return f'({self.lhs} & {self.rhs})'

class BitwiseOr(BinaryOp):
    def __str__(self):
        return f'({self.lhs} | {self.rhs})'

class BitwiseXor(BinaryOp):
    def __str__(self):
        return f'({self.lhs} ^ {self.rhs})'

class LessThan(BinaryOp):
    def __str__(self):
        return f'({self.lhs} < {self.rhs})'

class LessThanOrEquals(BinaryOp):
    def __str__(self):
        return f'({self.lhs} <= {self.rhs})'

class GreaterThan(BinaryOp):
    def __str__(self):
        return f'({self.lhs} > {self.rhs})'

class GreaterThanOrEquals(BinaryOp):
    def __str__(self):
        return f'({self.lhs} >= {self.rhs})'

class EqualTo(BinaryOp):
    def __str__(self):
        return f'({self.lhs} == {self.rhs})'

class NotEqualTo(BinaryOp):
    def __str__(self):
        return f'({self.lhs} != {self.rhs})'

class Concatenate(ModelExpr):
    def __init__(self, terms):
        self.terms = terms

    def __str__(self):
        return '{' + ', '.join(str(term) for term in self.terms) + '}'

class Case(ModelExpr):
    def __init__(self, terms, sel_bits):
        self.terms = terms
        self.sel_bits = sel_bits

    def settings2term(self, sel_bit_settings):
        return self.terms[self.settings2addr(sel_bit_settings)]

    def settings2addr(self, sel_bit_settings):
        bit_str = ''.join([str(sel_bit_settings[sel_bit.name]) for sel_bit in self.sel_bits])
        return int(bit_str, 2)

class ArrayOp(ModelExpr):
    def __init__(self, terms, addr):
        self.terms = terms
        self.addr = addr

class AnalogArray(ArrayOp):
    pass

class DigitalArray(ArrayOp):
    pass

class CaseExpr(ModelExpr):
    def __init__(self, cases):
        self.cases = cases

class AnalogCases(CaseExpr):
    pass

class DigitalCases(CaseExpr):
    pass

class Signal(ModelExpr):
    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        return self.name

class AnalogSignal(Signal):
    def __init__(self, name=None, range=None, copy_format_from=None):
        super().__init__(name=name)
        self.range = range
        self.copy_format_from = copy_format_from

    def copy_format_to(self, name):
        return AnalogSignal(name=name, copy_format_from=self)

class AnalogInput(AnalogSignal):
    pass

class AnalogOutput(AnalogSignal):
    pass

class DigitalSignal(Signal):
    def __init__(self, name=None, width=1, signed=False):
        super().__init__(name=name)
        self.width=width
        self.signed=signed

    def copy_format_to(self, name):
        return DigitalSignal(name=name, width=self.width, signed=self.signed)

class DigitalInput(DigitalSignal):
    pass

class DigitalOutput(DigitalSignal):
    pass

def main():
    a = Signal('a')
    b = Signal('b')

    expr = (a+b)/3
    print(expr)

if __name__ == '__main__':
    main()