from msdsl import AnalogSignal, distribute_mult
from msdsl.expr.simplify import extract_coeffs


def test_simplify():
    a = AnalogSignal('a')
    b = AnalogSignal('b')
    c = AnalogSignal('c')
    d = AnalogSignal('d')

    e = a-(b-12*(c-d))+b+34*c+46.5*d
    print('Original expression:')
    print(e)
    print('')

    f = distribute_mult(e)
    print('Flattened expresion:')
    print(f)
    print('')

    coeffs, others = extract_coeffs(f)
    print('Extracted coefficients (may contain repeats):')
    print([(coeff, signal.name) for coeff, signal in coeffs])
    print('')

    # make sure there are no unhandled terms
    assert len(others) == 0

    # sum up all of the coefficients for each signal
    signals = {}
    for coeff, signal in coeffs:
        if signal.name not in signals:
            signals[signal.name] = 0
        signals[signal.name] += coeff

    # check results
    print('Signal coefficients:')
    print(signals)
    assert signals == {
        'a': 1,
        'b': 0,
        'c': 46,
        'd': 34.5
    }
