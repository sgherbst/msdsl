from typing import List
from numbers import Number

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

class Constant(ModelExpr):
    def __init__(self, value: Number):
        self.value = value

class ListOp(ModelExpr):
    def __init__(self, terms: List[ModelExpr]):
        self.terms = terms

class Plus(ListOp):
    pass

class Times(ListOp):
    pass

class BinaryOp(ModelExpr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class LessThan(BinaryOp):
    pass

class LessThanOrEquals(BinaryOp):
    pass

class GreaterThan(BinaryOp):
    pass

class GreaterThanOrEquals(BinaryOp):
    pass

class EqualTo(BinaryOp):
    pass

class NotEqualTo(BinaryOp):
    pass

class Concatenate(ModelExpr):
    def __init__(self, terms):
        self.terms = terms

class AnalogArray(ModelExpr):
    def __init__(self, terms, addr):
        self.terms = terms
        self.addr = addr

class Signal(ModelExpr):
    def __init__(self, name=None):
        self.name = name

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