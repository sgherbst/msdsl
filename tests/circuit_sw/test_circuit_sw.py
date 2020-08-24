# general imports
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, AnalogSignal

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(rp1, rn1, rp2, rn2, real_type, dt=0.1e-6):
    # declare model
    m = MixedSignalModel('model', dt=dt, real_type=real_type)

    # declare I/O
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('sw1')
    m.add_digital_input('sw2')

    # declare switch circuit
    c = m.make_circuit()
    gnd = c.make_ground()
    c.voltage('net_v_in', gnd, m.v_in)
    c.switch('net_v_in', 'net_v_x', m.sw1, r_on=rp1, r_off=rn1)
    c.switch('net_v_x', gnd, m.sw2, r_on=rp2, r_off=rn2)
    c.add_eqns(
        AnalogSignal('net_v_x') == m.v_out
    )

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_binding(simulator, real_type, rp1=1.0, rn1=2.0, rp2=3.0, rn2=4.0):
    model_file = gen_model(rp1=rp1, rn1=rn1, rp2=rp2, rn2=rn2,
                           real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_circuit_sw'
        io = m.IO(
            v_in=fault.RealIn,
            v_out=fault.RealOut,
            sw1=m.BitIn,
            sw2=m.BitIn
        )

    t = MsdslTester(dut)

    def model(v_in, sw1, sw2):
        r_up = rp1 if sw1==1 else rn1
        r_dn = rp2 if sw2==1 else rn2
        return v_in * r_dn / (r_up + r_dn)

    def run_trial(v_in, sw1, sw2, should_print=True):
        t.poke(dut.v_in, v_in)
        t.poke(dut.sw1, sw1)
        t.poke(dut.sw2, sw2)
        t.eval()
        if should_print:
            t.print('v_in: %0f, sw1: %0d, sw2: %0d, v_out: %0f\n',
                    dut.v_in, dut.sw1, dut.sw2, dut.v_out)
        t.expect(dut.v_out, model(v_in, sw1, sw2), abs_tol=1e-3)

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
        ext_srcs=[model_file, get_file('circuit_sw/test_circuit_sw.sv')],
        real_type=real_type
    )
