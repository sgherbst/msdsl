from numpy import isclose
from msdsl import VerilogGenerator, AnalogSignal, distribute_mult
from msdsl.expr.expr import Sum, Product

def test_distribute_mult():
    a = AnalogSignal('a')
    b = AnalogSignal('b')
    c = AnalogSignal('c')
    d = AnalogSignal('d')

    e = a+3.4*(b+5.6*(c+7.8*d))
    print('Original expression:')
    print(e)
    print('')

    f = distribute_mult(e)
    print('Flattened expresion:')
    print(f)
    print('')

    v = VerilogGenerator()
    v.text = ''
    v.expr_to_signal(f)
    print('Compiled expression:')
    print(v.text)
    print('')

    # check that the flattened expression is OK
    assert(isinstance(f, Sum))
    res = {}
    for op in f.operands:
        if isinstance(op, Product):
            subops = op.operands
            sig = subops[0] if isinstance(subops[0], AnalogSignal) else subops[1]
            val = subops[1] if isinstance(subops[0], AnalogSignal) else subops[0]
            res[sig.name] = val.value
        elif isinstance(op, AnalogSignal):
            res[op.name] = 1.0
    print('Dictionary mapping signal names to coefficients:')
    print(res)
    assert len(res) == 4
    assert isclose(res['a'], 1)
    assert isclose(res['b'], 3.4)
    assert isclose(res['c'], 3.4*5.6)
    assert isclose(res['d'], 3.4*5.6*7.8)

if __name__ == '__main__':
    test_distribute_mult()
