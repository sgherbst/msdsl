# general imports
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, AnalogSignal

NAME = '_'.join(Path(__file__).stem.split('_')[1:])
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

# TODO: fix bug in which this test fails with r_off greater than or equal to 2.7e3
# The timestep doesn't really affect this particular bug, nor does the inductance,
# or the "ON" resistance of the switch.  Instead, the problem is related to the
# produce to "r_off" and "current_range".  If both switches are off, and the
# current through the inductor is actually at the specified limit, the output
# voltage could be enormous.  But this is unlikely to happen, so we need some
# way to (1) clamp internally to more reasonable values, and (2) detect when
# this problem is likely to occur.
def gen_model(r_off=2.6e3, current_range=100, real_type=RealType.FixedPoint):
    # declare model
    m = MixedSignalModel('model', dt=1e-9, real_type=real_type)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('sw1')
    m.add_digital_input('sw2')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    # create test circuit
    c = m.make_circuit(clk=m.clk, rst=m.rst)
    gnd = c.make_ground()
    c.voltage('net_v_in', gnd, m.v_in)
    c.switch('net_v_in', 'net_v_x', m.sw1, r_off=r_off)
    c.switch('net_v_x', gnd, m.sw2, r_off=r_off)
    c.inductor('net_v_in', 'net_v_x', 1.0, current_range=current_range)
    c.add_eqns(AnalogSignal('net_v_x') == m.v_out)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_circuit_ind_sw(simulator, real_type):
    model_file = gen_model(real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = f'test_{NAME}'
        io = m.IO(
            v_in=fault.RealIn,
            v_out=fault.RealOut,
            sw1=m.BitIn,
            sw2=m.BitIn,
            clk=m.ClockIn,
            rst=m.BitIn
        )

    t = MsdslTester(dut, dut.clk)

    # initialize
    t.poke(dut.v_in, 0.0)
    t.poke(dut.sw1, 0)
    t.poke(dut.sw2, 0)
    t.poke(dut.clk, 0)
    t.poke(dut.rst, 1)

    def model(v_in, sw1, sw2):
        if sw1 == 0 and sw2 == 0:
            return 0.5*v_in
        elif sw1 == 0 and sw2 == 1:
            return 0.0
        elif sw1 == 1 and sw2 == 0:
            return v_in
        elif sw1 == 1 and sw2 == 1:
            return 0.5*v_in
        else:
            raise Exception(f'Invalid switch values: sw1={sw1}, sw2={sw2}.')

    def run_trial(v_in, sw1, sw2, should_print=True):
        t.poke(dut.v_in, v_in)
        t.poke(dut.sw1, sw1)
        t.poke(dut.sw2, sw2)
        t.step(2)
        if should_print:
            t.print('v_in: %0f, sw1: %0d, sw2: %0d, v_out: %0f\n',
                    dut.v_in, dut.sw1, dut.sw2, dut.v_out)
        t.expect(dut.v_out, model(v_in, sw1, sw2), abs_tol=1e-2)

    # record tests
    v_in = 1.23
    run_trial(v_in, 0, 0)
    run_trial(v_in, 0, 1)
    run_trial(v_in, 1, 0)
    run_trial(v_in, 1, 1)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        real_type=real_type
    )
