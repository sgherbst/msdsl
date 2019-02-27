from msdsl.expr.expr import ModelExpr
from msdsl.expr.format import RealFormat, UIntFormat, SIntFormat
from msdsl.expr.svreal import RangeOf, WidthOf, ExponentOf, UndefinedRange

class Signal(ModelExpr):
    def __init__(self, name, format):
        self.name = name
        super().__init__(format=format)

    def __str__(self):
        return self.name

class AnalogSignal(Signal):
    def __init__(self, name, range=None, width=None, exponent=None):
        range = range if range is not None else UndefinedRange()
        format = RealFormat(range=range, width=width, exponent=exponent)
        super().__init__(name=name, format=format)

class AnalogState(AnalogSignal):
    def __init__(self, name, range, width=None, exponent=None, init=0):
        self.init = init
        super().__init__(name=name, range=range, width=width, exponent=exponent)

class AnalogOutput(AnalogSignal):
    def __init__(self, name, init=0):
        self.init = init
        super().__init__(name=name, range=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class AnalogInput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class DigitalSignal(Signal):
    def __init__(self, name, width=1, signed=False):
        # determine the foramt
        if signed:
            format = SIntFormat(width=width)
        else:
            format = UIntFormat(width=width)

        # call the super constructor
        super().__init__(name=name, format=format)

class DigitalState(DigitalSignal):
    def __init__(self, name, width=1, signed=False, init=0):
        self.init = init
        super().__init__(name=name, width=width, signed=signed)

class DigitalOutput(DigitalSignal):
    def __init__(self, name, width=1, signed=False, init=0):
        self.init = init
        super().__init__(name=name, width=width, signed=signed)

class DigitalInput(DigitalSignal):
    pass

def main():
    a = DigitalSignal('a', width=8, signed=True)
    b = AnalogSignal('b')

    expr = (a+b)/3
    print(expr)
    print(expr.format.range)

if __name__ == '__main__':
    main()