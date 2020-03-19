import numpy as np
import pytest
from pathlib import Path
from msdsl import Function

BUILD_DIR = Path(__file__).resolve().parent / 'build'

@pytest.mark.parametrize("order,err_limit,numel",
                         [(0, 0.06, 512),
                          (1, 0.0012, 128),
                          (2, 0.001, 32)])
def test_real_func(order, err_limit, numel):
    # function parameters
    testfun = np.sin
    domain = [-np.pi, +np.pi]

    # create the function
    func = Function(func=testfun, domain=domain, order=order, numel=numel)
    func.create_tables()

    # evaluate function approximation
    samp = np.random.uniform(domain[0], domain[1], 100)
    approx = func.eval_on(samp)

    # evaluate exact function
    exact = testfun(samp)

    # check error
    err = np.linalg.norm(exact-approx)
    print(f'RMS error with order={order}: {err}')
    assert err <= err_limit
