from msdsl.expr.format import SIntFormat, UIntFormat


def generic_test(cls, pairs):
    for x, width in pairs:
        assert cls.width_of(x) == width


def test_sint_width():
    pairs = []

    # simple tests
    pairs += [
        (0, 1),
        (1, 2),
        (2, 3),
        (-1, 1),
        (-2, 2),
        (-3, 3),
        (126, 8),
        (127, 8),
        (128, 9),
        (-127, 8),
        (-128, 8),
        (-129, 9)
    ]

    # stress tests
    for n in range(10, 100):
        pairs += [
            ((1<<(n-1))-2, n),
            ((1<<(n-1))-1, n),
            ((1<<(n-1))-0, n+1),
            ((1<<(n-1))+1, n+1),
            ((-(1<<(n-1)))+1, n),
            ((-(1<<(n-1)))-0, n),
            ((-(1<<(n-1)))-1, n+1),
            ((-(1<<(n-1)))-2, n+1)
        ]

    # run tests
    generic_test(cls=SIntFormat, pairs=pairs)


def test_uint_width():
    pairs = []

    # simple tests
    pairs += [
        (0, 1),
        (1, 1),
        (2, 2),
        (3, 2),
        (126, 7),
        (127, 7),
        (128, 8)
    ]

    # stress tests
    for n in range(10, 100):
        pairs += [
            ((1<<n)-2, n),
            ((1<<n)-1, n),
            ((1<<n)-0, n+1),
            ((1<<n)+1, n+1)
        ]

    # run tests
    generic_test(cls=UIntFormat, pairs=pairs)
