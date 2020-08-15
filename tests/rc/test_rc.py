# general imports
from math import exp
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, Deriv

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(tau, dt, real_type):
    model = MixedSignalModel('model', dt=dt, real_type=real_type)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out')
    model.add_digital_input('clk')
    model.add_digital_input('rst')

    model.add_eqn_sys([Deriv(model.v_out) == (model.v_in - model.v_out)/tau],
                      clk=model.clk, rst=model.rst)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    model.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_rc(simulator, real_type, tau=1e-6, dt=0.1e-6):
    model_file = gen_model(tau=tau, dt=dt, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name='test_rc'
        io=m.IO(
            v_in=fault.RealIn,
            v_out=fault.RealOut,
            clk=m.ClockIn,
            rst=m.BitIn
        )

    # create the tester
    tester = MsdslTester(dut, dut.clk)

    # initialize
    v_in = 1.0
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.poke(dut.v_in, v_in)
    tester.eval()

    # reset
    tester.step(2)

    # print the first few outputs
    tester.poke(dut.rst, 0)
    for k in range(20):
        tester.expect(dut.v_out, v_in*(1-exp(-k*dt/tau)), abs_tol=0.025)
        tester.print("v_out: %0f\n", dut.v_out)
        tester.step(2)

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('rc/test_rc.sv')],
        real_type=real_type
    )
