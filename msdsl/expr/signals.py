from msdsl.expr.expr import ModelExpr
from msdsl.expr.format import RealFormat, UIntFormat, SIntFormat
from msdsl.expr.range import RangeOf

class Signal(ModelExpr):
    def __init__(self, name=None, format=None):
        # save settings
        self.name = name

        # call the super constructor
        super().__init__(format=format)

    def __str__(self):
        return self.name

class AnalogSignal(Signal):
    def __init__(self, name, range=None, width=None):
        # set defaults
        if range is None:
            range = RangeOf(name)

        # determine the format
        format = RealFormat(range=range, width=width)

        # call the super constructor
        super().__init__(name=name, format=format)

class AnalogInput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range=RangeOf(name))

class AnalogOutput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range=RangeOf(name))

class DigitalSignal(Signal):
    def __init__(self, name, width=1, signed=False):
        # determine the foramt
        if signed:
            format = SIntFormat(width=width)
        else:
            format = UIntFormat(width=width)

        # call the super constructor
        super().__init__(name=name, format=format)

class DigitalInput(DigitalSignal):
    pass

class DigitalOutput(DigitalSignal):
    pass

def main():
    a = DigitalSignal('a', width=8, signed=True)
    b = AnalogSignal('b')

    expr = (a+b)/3
    print(expr)
    print(expr.format.range)

if __name__ == '__main__':
    main()