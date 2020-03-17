from pathlib import Path
import numpy as np
from msdsl import Function

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def test_real_func():
    # function parameters
    testfun = np.sin
    domain = [-np.pi, +np.pi]

    # create the function
    func = Function(func=testfun, domain=domain)
    func.create_tables()

    # evaluate
    samp = np.random.uniform(domain[0], domain[1], 100)
    approx = func.eval_on(samp)
    exact = testfun(samp)

    print(np.max(np.abs(exact-approx)))