from msdsl import VerilogGenerator, AnalogSignal, distribute_mult

def main():
    a = AnalogSignal('a')
    b = AnalogSignal('b')
    c = AnalogSignal('c')
    d = AnalogSignal('d')

    e = 1.2*(a+3.4*(b+5.6*(c+7.8*d)))

    print('Original expression:')
    print(e)
    print('')

    print('Expression after flattening:')
    print(distribute_mult(e))
    print('')

    print('Compiled expression')
    v = VerilogGenerator()
    v.text = ''
    v.expr_to_signal(distribute_mult(e))
    print(v.text)

if __name__ == '__main__':
    main()