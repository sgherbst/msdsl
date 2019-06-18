from msdsl.expr.signals import AnalogSignal, Signal
from msdsl.expr.svreal import UndefinedRange

def deriv_str(name):
    return 'Deriv(' + name + ')'

class Deriv(AnalogSignal):
    """
    Container for a derivative used within MSDSL.
    """
    def __init__(self, signal: Signal):
        self.signal = signal
        super().__init__(name=deriv_str(signal.name), range_=UndefinedRange())

def main():
    x = AnalogSignal('x')
    y = AnalogSignal('y')

    print(Deriv(x) + y + 1)

if __name__ == '__main__':
    main()