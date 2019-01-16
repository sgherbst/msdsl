from typing import List
from numbers import Number

class ModelExpr:
    # addition
    def __add__(self, other):
        if isinstance(other, Number):
            other = Constant(other)

        if isinstance(other, ModelExpr):
            return Plus([self, other])
        else:
            raise NotImplementedError

    def __radd__(self, other):
        return self.__add__(other)

    # multiplication
    def __mul__(self, other):
        if isinstance(other, Number):
            other = Constant(other)

        if isinstance(other, ModelExpr):
            return Times([self, other])
        else:
            raise NotImplementedError

    def __rmul__(self, other):
        return self.__mul__(other)

    # subtraction
    def __sub__(self, other):
        return self.__add__(-other)

    def __rsub__(self, other):
        return (-self).__add__(other)

    # negation
    def __neg__(self):
        return -1.0*self

    # division
    def __truediv__(self, other):
        return (1.0/other)*self

class Plus(ModelExpr):
    def __init__(self, terms: List[ModelExpr]):
        self.terms = terms

class Times(ModelExpr):
    def __init__(self, terms: List[ModelExpr]):
        self.terms = terms

class Constant(ModelExpr):
    def __init__(self, value: Number):
        self.value = value

class AnalogArray(ModelExpr):
    def __init__(self, values, addr):
        self.values = values
        self.addr = addr

class Signal(ModelExpr):
    def __init__(self, name=None):
        self.name = name

class AnalogSignal(Signal):
    def __init__(self, name=None, range=None):
        super().__init__(name=name)
        self.range = range

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