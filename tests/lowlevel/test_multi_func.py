# general imports
import numpy as np
import importlib
from pathlib import Path

# msdsl imports
from ..common import pytest_sim_params
from msdsl import MultiFunction

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    tests = [(0, 0.0105, 512),
             (1, 0.000318, 128)]
    if importlib.util.find_spec('cvxpy'):
        tests.append((2, 0.000232, 32))
    metafunc.parametrize('order,err_lim,numel', tests)

def test_multi_func(order, err_lim, numel):
    # set the random seed for repeatable results
    np.random.seed(0)

    # function parameters
    domain = [-np.pi, +np.pi]
    test_funcs = [
        lambda x: np.sin(np.clip(x, domain[0], domain[1])),
        lambda x: np.cos(np.clip(x, domain[0], domain[1]))
    ]

    # create the function
    func = MultiFunction(func=test_funcs, domain=domain, order=order, numel=numel)

    # evaluate function approximation
    samp = np.random.uniform(1.2*domain[0], 1.2*domain[1], 1000)
    meas = func.eval_on(samp)

    # evaluate exact function
    expt = [test_func(samp) for test_func in test_funcs]

    # check error
    errs = np.array([np.sqrt(np.mean((m-e)**2)) for m, e in zip(meas, expt)])
    print(f'RMS errors with order={order}: {errs}')
    assert np.all(errs <= err_lim)
