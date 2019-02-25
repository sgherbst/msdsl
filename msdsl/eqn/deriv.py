from msdsl.expr.signals import AnalogSignal

def deriv_str(name):
    return 'Deriv(' + name + ')'

class Deriv(AnalogSignal):
    def __init__(self, signal: AnalogSignal):
        self.signal = signal
        super().__init__(name=deriv_str(signal.name))

def main():
    x = AnalogSignal('x')
    y = AnalogSignal('y')

    print(Deriv(x) + y + 1)

if __name__ == '__main__':
    main()