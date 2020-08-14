import pytest
from msdsl.lfsr import LFSR

@pytest.mark.parametrize('n', list(range(3, 19)))
def test_lsfr(n):
    lfsr = LFSR(n)
    state = 0

    passes = []
    for i in range(2):
        passes.append([])
        for _ in range((1<<n)-1):
            passes[-1].append(state)
            state = lfsr.next_state(state)

    # check that all numbers were covered in the first pass
    assert sorted(passes[0]) == list(range((1<<n)-1))

    # check that the first pass is exactly equal to the second pass
    assert passes[0] == passes[1]
