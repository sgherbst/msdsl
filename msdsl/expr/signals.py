from msdsl.expr.expr import ModelExpr
from msdsl.expr.format import RealFormat, UIntFormat, SIntFormat, is_signed
from msdsl.expr.svreal import RangeOf, WidthOf, ExponentOf, UndefinedRange

class Signal(ModelExpr):
    def __init__(self, name, format_):
        self.name = name
        super().__init__(format_=format_)

    def __str__(self):
        return self.name

class AnalogSignal(Signal):
    def __init__(self, name, range_=None, width=None, exponent=None):
        range_ = range_ if range_ is not None else UndefinedRange()
        format_ = RealFormat(range_=range_, width=width, exponent=exponent)
        super().__init__(name=name, format_=format_)

class AnalogState(AnalogSignal):
    def __init__(self, name, range_, width=None, exponent=None, init=0):
        self.init = init
        super().__init__(name=name, range_=range_, width=width, exponent=exponent)

class AnalogOutput(AnalogSignal):
    def __init__(self, name, init=0):
        self.init = init
        super().__init__(name=name, range_=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class AnalogInput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range_=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class DigitalSignal(Signal):
    def __init__(self, name, width=1, signed=False):
        # determine the foramt
        if signed:
            format_ = SIntFormat(width=width)
        else:
            format_ = UIntFormat(width=width)

        # call the super constructor
        super().__init__(name=name, format_=format_)

    @property
    def width(self):
        return self.format_.width

    @property
    def signed(self):
        return is_signed(self.format_)

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
    print(expr.format_.range_)

if __name__ == '__main__':
    main()