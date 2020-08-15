# general imports
from pathlib import Path
import numpy as np

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(real_type):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR, real_type=real_type)
    model.add_digital_input('clk')
    model.add_digital_input('rst')
    model.add_analog_output('real_out')

    model.set_this_cycle(model.real_out, model.uniform_signal(clk=model.clk, rst=model.rst))

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_uniform(simulator, real_type, n_trials=10000):
    # generate model
    model_file = gen_model(real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_uniform'
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

    # print the first few outputs
    data = []
    for _ in range(n_trials):
        data.append(t.get_value(dut.real_out))
        t.step(2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('uniform/test_uniform.sv')],
        real_type=real_type
    )

    # analyze the data
    data = np.array([elem.value for elem in data], dtype=float)
    mean = np.mean(data)
    std = np.std(data)
    min_val = np.min(data)
    max_val = np.max(data)
    print(f"mean: {mean}, standard dev: {std}, min: {min_val}, max: {max_val}")

    # check the results
    assert 0.49 <= mean <= 0.51, 'Mean is unexpected.'
    assert 0.27 <= std <= 0.31, 'Standard deviation is unexpected.'
    assert 0 <= min_val <= 0.01, 'Minimum value is unexpected.'
    assert 0.99 <= max_val <= 1.0, 'Maximum value is unexpected.'
