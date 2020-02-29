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
from msdsl import MixedSignalModel, VerilogGenerator, RangeOf, AnalogSignal, get_msdsl_header

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(res=1e3, cap=1e-9, dt=0.1e-6):
    m = MixedSignalModel('model', dt=dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    c = m.make_circuit(clk=m.clk, rst=m.rst)
    gnd = c.make_ground()

    c.capacitor('net_v_out', gnd, cap, voltage_range=RangeOf(m.v_out))
    c.resistor('net_v_in', 'net_v_out', res)
    c.voltage('net_v_in', gnd, m.v_in)

    c.add_eqns(
        AnalogSignal('net_v_out') == m.v_out
    )

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_circuit_rc(simulator, res=1e3, cap=1e-9, dt=0.1e-6):
    model_file = gen_model(res=res, cap=cap, dt=dt)

    # declare circuit
    dut = m.DeclareCircuit(
        'test_circuit_rc',
        'v_in', fault.RealIn,
        'v_out', fault.RealOut,
        'clk', m.BitIn,
        'rst', m.BitIn
    )

    # create the tester
    tester = fault.Tester(dut, expect_strict_default=True)

    def cycle():
        tester.poke(dut.clk, 1)
        tester.eval()
        tester.poke(dut.clk, 0)
        tester.eval()

    # initialize
    v_in = 1.0
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.poke(dut.v_in, v_in)
    tester.eval()

    # reset
    cycle()

    # model for circuit behavior
    def model(t):
        return v_in*(1-exp(-t/(res*cap)))

    # print the first few outputs
    tester.poke(dut.rst, 0)
    for k in range(20):
        tester.expect(dut.v_out, model(k*dt), abs_tol=0.025)
        tester.print("v_out: %0f\n", dut.v_out)
        cycle()

    # run the simulation
    tester.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('circuit_rc/test_circuit_rc.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )