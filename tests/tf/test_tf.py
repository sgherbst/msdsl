# general imports
from math import exp
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

NAME = Path(__file__).stem.split('_')[1]
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(tau=1e-6, dt=0.1e-6, real_type=RealType.FixedPoint):
    m = MixedSignalModel('model', dt=dt, real_type=real_type)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    m.set_tf(input_=m.v_in, output=m.v_out, tf=((1,), (tau, 1)), clk=m.clk, rst=m.rst)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_tf(simulator, real_type, tau=1e-6, dt=0.1e-6):
    model_file = gen_model(tau=tau, dt=dt, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name=f'test_{NAME}'
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

    # model for circuit behavior
    def model(t):
        return v_in*(1-exp(-t/tau))

    # print the first few outputs
    tester.poke(dut.rst, 0)
    tester.step(2) # TODO: figure out why an extra cycle is needed here
    for k in range(20):
        tester.expect(dut.v_out, model(k*dt), abs_tol=0.025)
        tester.print("v_out: %0f\n", dut.v_out)
        tester.step(2)

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        real_type=real_type
    )
