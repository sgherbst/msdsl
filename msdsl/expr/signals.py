from numbers import Number

from msdsl.expr.expr import ModelExpr
from msdsl.expr.format import RealFormat, UIntFormat, SIntFormat, is_signed
from msdsl.expr.svreal import RangeOf, WidthOf, ExponentOf, UndefinedRange, ParamRange

class Signal(ModelExpr):
    def __init__(self, name, format_):
        self.name = name
        super().__init__(format_=format_)

    def __str__(self):
        return self.name

class AnalogSignal(Signal):
    """
    The AnalogSignal object is used within MSDSL to represent an analog signal. Any analog signal that shall be used
    withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the analog signal to be added
    :param range_:      Range of the analog signal. Note that the range will be considered for positive and negative values.
    :param width:       Specify a width different from the default.
    :param exponent:    Specify an exponent different from the default. Usually this is automatically calculated.
    """
    def __init__(self, name, range_=None, width=None, exponent=None):
        range_ = range_ if range_ is not None else UndefinedRange()
        format_ = RealFormat(range_=range_, width=width, exponent=exponent)
        super().__init__(name=name, format_=format_)

class AnalogState(AnalogSignal):
    """
    The AnalogState object is used within MSDSL to represent an analog state such as the voltage of a capacitor. Any
    analog state that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the analog state to be added
    :param range_:      Range of the analog signal. Note that the range will be considered for positive and negative values.
    :param width:       Specify a width different from the default.
    :param exponent:    Specify an exponent different from the default. Usually this is automatically calculated.
    :param init:        Initial value of the analog state.
    """
    def __init__(self, name, range_, width=None, exponent=None, init=0):
        self.init = init
        super().__init__(name=name, range_=range_, width=width, exponent=exponent)

class AnalogOutput(AnalogSignal):
    """
    The AnalogOutput object is used within MSDSL to represent an analog output such as the voltage of a capacitor. Any
    analog output that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the analog signal to be added
    :param init:        Initial value of the analog output.
    """
    def __init__(self, name, init=0):
        self.init = init
        super().__init__(name=name, range_=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class AnalogInput(AnalogSignal):
    """
    The AnalogInput object is used within MSDSL to represent an analog input such as the voltage of a capacitor. Any
    analog output that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the analog signal to be added
    """
    def __init__(self, name):
        super().__init__(name=name, range_=RangeOf(name), width=WidthOf(name), exponent=ExponentOf(name))

class RealParameter(AnalogSignal):
    def __init__(self, param_name, signal_name, default=0):
        self.param_name = param_name
        self.default = default
        super().__init__(name=signal_name, range_=ParamRange(param_name))

    @property
    def signal_name(self):
        return self.name

class DigitalSignal(Signal):
    """
    The DigitalSignal object is used within MSDSL to represent a digital signal. Any digital signal that shall be used
    withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the digital signal to be added
    :param width:       Specify a width different from the default.
    :param signed:      Setting this option to True will change from the unsigned, default representation to a signed one.
    :param min_val:     Minimum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    :param max_val:     Maximum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    """
    def __init__(self, name, width=1, signed=False, min_val=None, max_val=None):
        # determine the foramt
        if signed:
            format_ = SIntFormat(width=width, min_val=min_val, max_val=max_val)
        else:
            format_ = UIntFormat(width=width, min_val=min_val, max_val=max_val)

        # call the super constructor
        super().__init__(name=name, format_=format_)

    @property
    def width(self):
        return self.format_.width

    @property
    def signed(self):
        return is_signed(self.format_)

class DigitalParameter(DigitalSignal):
    """
    :param name:        Name of the digital parameter to be added
    :param width:       Specify a width different from the default.
    :param signed:      Setting this option to True will change from the unsigned, default representation to a signed one.
    :param default:     Default value of the parameter if not specified.
    :param min_val:     Minimum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    :param max_val:     Maximum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    """
    def __init__(self, name, width=1, signed=False, default=0, min_val=None, max_val=None):
        # call the super constructor
        super().__init__(name=name, width=width, signed=signed, min_val=min_val, max_val=max_val)

        # check that the default value can be properly represented given the formatting of this parameter
        # if the user provides the default as a string (e.g., "16'ABCD", "param1+param2"), the bounds are
        # not currently checked
        if isinstance(default, Number):
            assert self.format_.min_val <= default <= self.format_.max_val, \
                f'Default value {default} is not in range [{self.format_.min_val}, {self.format_.max_val}].'
        else:
            print(f'Warning: could not validate bounds for default value of parameter {name}')

        # save the default
        self.default = default

class DigitalState(DigitalSignal):
    """
    The DigitalState object is used within MSDSL to represent a digital state. Any
    digital state that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the digital state to be added
    :param width:       Specify a width different from the default.
    :param signed:      Setting this option to True will change from the unsigned, default representation to a signed one.
    :param init:        Initial value of the analog state.
    :param min_val:     Minimum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    :param max_val:     Maximum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    """
    def __init__(self, name, width=1, signed=False, init=0, min_val=None, max_val=None):
        self.init = init
        super().__init__(name=name, width=width, signed=signed, min_val=min_val, max_val=max_val)

class DigitalOutput(DigitalSignal):
    """
    The DigitalOutput object is used within MSDSL to represent an digital output such as the output of a logic gate. Any
    digital output that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the digital signal to be added
    :param width:       Specify a width different from the default.
    :param signed:      Setting this option to True will change from the unsigned, default representation to a signed one.
    :param init:        Initial value of the analog output.
    :param min_val:     Minimum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    :param max_val:     Maximum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    """
    def __init__(self, name, width=1, signed=False, init=0, min_val=None, max_val=None):
        self.init = init
        super().__init__(name=name, width=width, signed=signed, min_val=min_val, max_val=max_val)

class DigitalInput(DigitalSignal):
    """
    The DigitalInput object is used within MSDSL to represent an digital input such as the input of a logic gate. Any
    digital input that shall be used withing the functional model generated via MSDSL needs to be an instance of this class.

    :param name:        Name of the analog signal to be added
    :param width:       Specify a width different from the default.
    :param signed:      Setting this option to True will change from the unsigned, default representation to a signed one.
    :param min_val:     Minimum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    :param max_val:     Maximum value of the signal.  You should generally leave this as "None" so that it will be
                        filled in automatically.
    """
    pass

def main():
    a = DigitalSignal('a', width=8, signed=True)
    b = AnalogSignal('b')

    expr = (a+b)/3
    print(expr)
    print(expr.format_.range_)

if __name__ == '__main__':
    main()