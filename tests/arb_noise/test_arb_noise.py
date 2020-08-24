# general imports
from pathlib import Path
import numpy as np
from scipy.stats import truncnorm

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(mean=0.0, std=1.0, num_sigma=6.0, order=1, numel=512,
              real_type=RealType.FixedPoint):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR, real_type=real_type)
    model.add_digital_input('clk')
    model.add_digital_input('rst')
    model.add_analog_output('real_out')

    # compute the inverse CDF of the distribution (truncated to 0, 1 domain)
    inv_cdf = lambda x: truncnorm.ppf(x, -num_sigma, +num_sigma, loc=mean, scale=std)

    # create the function object
    inv_cdf_func = model.make_function(inv_cdf, domain=[0.0, 1.0], order=order, numel=numel)

    model.set_this_cycle(model.real_out, model.arbitrary_noise(inv_cdf_func, clk=model.clk, rst=model.rst))

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_arb_noise(simulator, real_type, n_trials=10000):
    # generate model
    model_file = gen_model(mean=1.23, std=0.456, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_arb_noise'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            real_out=fault.RealOut
        )

    # create the tester
    t = MsdslTester(dut, dut.clk)

    # initialize
    t.poke(dut.clk, 0)
    t.poke(dut.rst, 1)
    t.step(2)
    t.poke(dut.rst, 0)
    t.step(2)

    # print the first few outputs
    data = []
    for _ in range(n_trials):
        data.append(t.get_value(dut.real_out))
        t.step(2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('arb_noise/test_arb_noise.sv')],
        real_type=real_type
    )

    # analyze the data
    data = np.array([elem.value for elem in data], dtype=float)
    mean = np.mean(data)
    std = np.std(data)
    min_val = np.min(data)
    max_val = np.max(data)
    print(f"mean: {mean}, standard dev: {std}, min: {min_val}, max: {max_val}")

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.hist(data, bins=50)
    # plt.show()

    # check the results
    assert 1.1 <= mean <= 1.3, 'Mean is unexpected.'
    assert 0.4 <= std <= 0.5, 'Standard deviation is unexpected.'
    assert -1.6 <= min_val, 'Minimum value is unexpected.'
    assert max_val <= 4.1, 'Maximum value is unexpected.'
