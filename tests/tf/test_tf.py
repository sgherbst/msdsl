# general imports
from math import exp
from pathlib import Path

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, get_msdsl_header

NAME = Path(__file__).stem.split('_')[1]
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(tau=1e-6, dt=0.1e-6):
    m = MixedSignalModel('model', dt=dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    m.set_tf(input_=m.v_in, output=m.v_out, tf=((1,), (tau, 1)), clk=m.clk, rst=m.rst)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_tf(simulator, tau=1e-6, dt=0.1e-6):
    model_file = gen_model(tau=tau, dt=dt)

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
    tester = fault.Tester(dut, dut.clk)

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
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )
