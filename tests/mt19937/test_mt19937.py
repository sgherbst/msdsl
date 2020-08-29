# general imports
import random
import numpy as np
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc, ['iverilog'])

def test_mt19937(simulator):
    # initialize seed for repeatable results
    random.seed(1)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_mt19937'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            seed=m.In(m.Bits[32]),
            out=m.Out(m.Bits[32])
        )

    # determine initial seed
    seed = random.randint(0, (1<<32)-1)
    print(f'Using seed: {seed}')

    t = MsdslTester(dut, dut.clk)

    # set the seed and reset
    t.zero_inputs()
    t.poke(dut.seed, seed)
    t.poke(dut.rst, 1)
    t.step(2)

    # clear reset
    t.poke(dut.rst, 0)
    t.step(2)

    # wait for RNG startup, which takes a long time...
    for _ in range(25000):
        t.step(2)

    # read some outputs
    data = []
    for _ in range(10000):
        data.append(t.get_value(dut.out))
        t.step(2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[THIS_DIR / 'test_mt19937.sv']
    )

    # extract results
    data = [elem.value/(1<<32) for elem in data]

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.hist(data, bins=50)
    # plt.show()

    # get mean and standard deviation
    mean = np.mean(data)
    std = np.std(data)
    print(f"mean: {mean}, standard dev: {std}")

    # construct empirical CDF
    data_sorted = np.sort(data)
    p = 1. * np.arange(len(data)) / (len(data) - 1)

    # read out the CDF at multiples of the standard deviation
    test_pts = np.linspace(0, 0.9, 10)
    meas_cdf = np.interp(test_pts, data_sorted, p)
    print(f'meas_cdf: {meas_cdf}')

    # determine what values the CDF should have at those points
    expct_cdf = test_pts
    print(f'expct_cdf: {expct_cdf}')

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.plot(test_pts, meas_cdf)
    # plt.plot(test_pts, expct_cdf)
    # plt.legend(['meas_cdf', 'expct_cdf'])
    # plt.show()

    # check the results
    assert np.isclose(mean, 0.5, rtol=0.05), 'Mean is unexpected.'
    assert np.isclose(std, 1/np.sqrt(12), rtol=0.05), 'Standard deviation is unexpected.'
    for k in range(len(test_pts)):
        assert np.isclose(meas_cdf[k], expct_cdf[k], rtol=0.05), \
            f'CDF mismatch at index {k}: {meas_cdf[k]} vs {expct_cdf[k]}'