# this test is adapted from:
# https://code.stanford.edu/ee272/ee272-hw6/-/blob/master/sim/filter/filter_tb.sv

# general imports
from pathlib import Path
import numpy as np

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

BUILD_DIR = Path(__file__).resolve().parent / 'build'
DOMAIN = np.pi
RANGE = 1.0

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(tau, real_type):
    # create mixed-signal model
    m = MixedSignalModel('model', build_dir=BUILD_DIR,
                         real_type=real_type)

    # define I/O
    x = m.add_analog_input('x')
    dt = m.add_analog_input('dt')
    y = m.add_analog_output('y')
    clk = m.add_digital_input('clk')
    rst = m.add_digital_input('rst')

    # create function
    func = m.make_function(lambda t: np.exp(-t/tau), domain=[0, 1e-6], order=1)

    # apply function
    f = m.set_from_sync_func('f', func, dt, clk=clk, rst=rst)

    # update output
    x_prev = m.cycle_delay(x, 1, clk=clk, rst=rst)
    y_prev = m.cycle_delay(y, 1, clk=clk, rst=rst)
    m.set_this_cycle(y, f*y_prev + (1-f)*x_prev)

    # write the model
    return m.compile_to_file(VerilogGenerator())

def test_var_timestep(simulator, real_type, tau=123e-9):
    # set the random seed for repeatable results
    np.random.seed(0)

    # generate model
    model_file = gen_model(tau=tau, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_var_timestep'
        io = m.IO(
            x=fault.RealIn,
            dt=fault.RealIn,
            y=fault.RealOut,
            clk=m.In(m.Clock),
            rst=m.BitIn
        )

    # create the tester
    t = MsdslTester(dut, dut.clk)

    # convenience function
    def check_out_is(val):
        t.print(f'meas=%0f, expct={val}\n', dut.y)
        t.expect(dut.y, val, abs_tol=2.5e-4)

    # initialize
    t.zero_inputs()
    t.poke(dut.rst, 1)

    # apply reset
    t.step(2)

    # clear reset
    t.poke(dut.rst, 0)
    t.step(4)

    # test 1: step response from t=0
    t.poke(dut.x, 1.23)
    t.poke(dut.dt, 234e-9)
    t.step(2)

    check_out_is(1.04647875745617)

    # test 2: intermediate value change
    t.poke(dut.x, 3.45)
    t.poke(dut.dt, 45.6e-9)
    t.step(2)
    t.poke(dut.x, -5.67)
    t.poke(dut.dt, 67.8e-9)
    t.step(2)

    check_out_is(-1.37061245526685)

    # test 3: successive updates
    t.poke(dut.dt, 78.9e-9)
    t.step(2)

    check_out_is(-3.40628070473501)

    t.poke(dut.dt, 89.1e-9)
    t.step(2)

    check_out_is(-4.57295640296259)

    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('var_timestep/test_var_timestep.sv')],
        real_type=real_type
    )
