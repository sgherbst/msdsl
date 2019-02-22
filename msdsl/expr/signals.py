from msdsl.expr.expr import ModelExpr
from msdsl.expr.format import RealFormat, IntegerFormat
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
    def __init__(self, name, range=None):
        super().__init__(name=name, format=RealFormat(range=range))

class AnalogInput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range=RangeOf(name))

class AnalogOutput(AnalogSignal):
    def __init__(self, name):
        super().__init__(name=name, range=RangeOf(name))

class DigitalSignal(Signal):
    def __init__(self, name, width=None, signed=None):
        super().__init__(name=name, format=IntegerFormat(width=width, signed=signed))

class DigitalInput(DigitalSignal):
    pass

class DigitalOutput(DigitalSignal):
    pass

def main():
    a = AnalogSignal('a', 30)
    b = AnalogSignal('b', 60)

    expr = (a+b)/3
    print(expr)
    print(expr.format.range)

if __name__ == '__main__':
    main()