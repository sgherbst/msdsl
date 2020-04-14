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
from msdsl import MixedSignalModel, VerilogGenerator, Deriv, get_msdsl_header

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(tau, dt):
    model = MixedSignalModel('model', dt=dt)
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

def test_rc(simulator, tau=1e-6, dt=0.1e-6):
    model_file = gen_model(tau=tau, dt=dt)

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
    tester = fault.Tester(dut, dut.clk)

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
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('rc/test_rc.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )
