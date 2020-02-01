# general imports
from math import exp, cos, sin, sqrt
from pathlib import Path

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, eqn_case, Deriv

NAME = Path(__file__).stem.split('_')[1]
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(tau_f=1e-9, tau_s=100e-9, dt=10e-9):
    m = MixedSignalModel('model', dt=dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    m.bind_name('in_gt_out', m.v_in > m.v_out)

    # detector dynamics
    eqns = [
        Deriv(m.v_out) == eqn_case([0, 1 / tau_f], [m.in_gt_out]) * (m.v_in - m.v_out) - (m.v_out / tau_s)
    ]
    m.add_eqn_sys(eqns,clk=m.clk, rst=m.rst)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_det(simulator, tau_f=1e-9, tau_s=100e-9, dt=10e-9):
    model_file = gen_model(tau_f=tau_f, tau_s=tau_s, dt=dt)

    # declare circuit
    dut = m.DeclareCircuit(
        f'test_{NAME}',
        'v_in', fault.RealIn,
        'v_out', fault.RealOut,
        'clk', m.BitIn,
        'rst', m.BitIn
    )

    # create the tester
    tester = fault.Tester(dut)

    def cycle(n=1):
        for _ in range(n):
            tester.poke(dut.clk, 1)
            tester.eval()
            tester.poke(dut.clk, 0)
            tester.eval()

    def debug():
        tester.print("v_in: %0f, v_out: %0f\n", dut.v_in, dut.v_out)

    # initialize
    v_in = 0.0
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.poke(dut.v_in, v_in)
    cycle()

    # clear reset
    tester.poke(dut.rst, 0)
    cycle()

    # check initial values
    debug()
    tester.expect(dut.v_out, 0.0, abs_tol=1e-3)

    # poke input
    tester.poke(dut.v_in, 1.5)
    cycle()
    debug()
    tester.expect(dut.v_out, 1.5, abs_tol=0.1)

    # clear input and make sure output is still high
    tester.poke(dut.v_in, 0.0)
    cycle()
    debug()
    tester.expect(dut.v_out, 1.4, abs_tol=0.1)

    # wait longer for output to decay back to zero
    cycle(30)
    debug()
    tester.expect(dut.v_out, 0.0, abs_tol=0.1)

    # poke input again
    tester.poke(dut.v_in, 1.5)
    cycle()
    debug()
    tester.expect(dut.v_out, 1.5, abs_tol=0.1)

    # this time set input to a mid-range value
    tester.poke(dut.v_in, 0.5)
    cycle()
    debug()
    tester.expect(dut.v_out, 1.4, abs_tol=0.1)

    # wait longer for output to decay to new input
    cycle(30)
    debug()
    tester.expect(dut.v_out, 0.5, abs_tol=0.1)

    # increase input and make sure output tracks immediately
    tester.poke(dut.v_in, 2.5)
    cycle()
    debug()
    tester.expect(dut.v_out, 2.5, abs_tol=0.1)

    # run the simulation
    tester.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        inc_dirs=[get_svreal_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )
