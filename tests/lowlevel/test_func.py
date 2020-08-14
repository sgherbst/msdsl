# general imports
import numpy as np
import importlib
from pathlib import Path

# msdsl imports
from ..common import pytest_sim_params
from msdsl import Function

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    tests = [(0, 0.0105, 512),
             (1, 0.000318, 128)]
    if importlib.util.find_spec('cvxpy'):
        tests.append((2, 0.000232, 32))
    metafunc.parametrize('order,err_lim,numel', tests)

def test_real_func(order, err_lim, numel):
    # set the random seed for repeatable results
    np.random.seed(0)

    # function parameters
    testfun = np.sin
    domain = [-np.pi, +np.pi]

    # create the function
    func = Function(func=testfun, domain=domain, order=order, numel=numel)

    # evaluate function approximation
    samp = np.random.uniform(domain[0], domain[1], 100)
    approx = func.eval_on(samp)

    # evaluate exact function
    exact = testfun(samp)

    # check error
    err = np.sqrt(np.mean((exact-approx)**2))
    print(f'RMS error with order={order}: {err}')
    assert err <= err_lim
