# general imports
from pathlib import Path
import random
import numpy as np
from scipy.stats import norm

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)
    metafunc.parametrize('gen_type', ['lcg', 'mt19937', 'lfsr'])

def gen_model(real_type, gen_type):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR, real_type=real_type)
    model.add_digital_input('clk')
    model.add_digital_input('rst')
    model.add_analog_input('mean_in')
    model.add_analog_input('std_in')
    model.add_analog_output('real_out')

    # apply noise
    model.set_gaussian_noise(model.real_out, std=model.std_in, mean=model.mean_in,
                             clk=model.clk, rst=model.rst, gen_type=gen_type)

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_gaussian_noise(simulator, real_type, gen_type,
                        n_trials=10000, mean_val=1.23, std_val=0.456):
    # set the random seed for repeatable results.  some code uses
    # numpy for random number generation, and some code uses the
    # random package, so both have to be set
    np.random.seed(1)
    random.seed(1)

    # generate model
    model_file = gen_model(real_type=real_type, gen_type=gen_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_gaussian_noise'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            mean_in=fault.RealIn,
            std_in=fault.RealIn,
            real_out=fault.RealOut
        )

    # create the tester
    t = MsdslTester(dut, dut.clk)

    # initialize
    t.zero_inputs()
    t.poke(dut.mean_in, mean_val)
    t.poke(dut.std_in, std_val)
    t.poke(dut.rst, 1)
    t.step(2)

    # clear reset and wait for RNG to start
    # this take a long time when using the MT19937 option
    t.poke(dut.rst, 0)
    if gen_type=='mt19937':
        wait_time = 25000
    else:
        wait_time = 100
    for _ in range(wait_time):
        t.step(2)

    # gather data
    data = []
    for _ in range(n_trials):
        data.append(t.get_value(dut.real_out))
        t.step(2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('gaussian_noise/test_gaussian_noise.sv')],
        real_type=real_type
    )

    # analyze the data
    data = np.array([elem.value for elem in data], dtype=float)
    mean = np.mean(data)
    std = np.std(data)
    print(f"mean: {mean}, standard dev: {std}")

    # construct empirical CDF
    data_sorted = np.sort(data)
    p = 1. * np.arange(len(data)) / (len(data) - 1)

    # read out the CDF at multiples of the standard deviation
    test_pts = std_val*np.arange(-2, 3) + mean_val
    meas_cdf = np.interp(test_pts, data_sorted, p)
    print(f'meas_cdf: {meas_cdf}')

    # determine what values the CDF should have at those points
    expct_cdf = norm.cdf(test_pts, mean_val, std_val)
    print(f'expct_cdf: {expct_cdf}')

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.hist(data, bins=50)
    # plt.show()

    # check the results
    assert np.isclose(mean, mean_val, rtol=0.05), 'Mean is unexpected.'
    assert np.isclose(std, std_val, rtol=0.05), 'Standard deviation is unexpected.'
    for k in range(len(test_pts)):
        assert np.isclose(meas_cdf[k], expct_cdf[k], rtol=0.15), \
            f'CDF mismatch at index {k}: {meas_cdf[k]} vs {expct_cdf[k]}'
