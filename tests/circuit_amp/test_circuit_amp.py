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

def gen_model(real_type, gain=123, dt=0.1e-6):
    # declare model
    m = MixedSignalModel('model', dt=dt, real_type=real_type)

    # declare I/O
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    # declare buffer circuit using negative feedback
    c = m.make_circuit()
    gnd = c.make_ground()
    c.voltage('net_v_in', gnd, m.v_in)
    c.vcvs('net_v_in', 'net_v_out', 'net_v_out', gnd, gain)
    c.add_eqns(
        AnalogSignal('net_v_out') == m.v_out
    )

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_amp(simulator, real_type, gain=123):
    model_file = gen_model(gain=gain, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_circuit_amp'
        io = m.IO(
            v_in=fault.RealIn,
            v_out=fault.RealOut
        )

    t = MsdslTester(dut)

    def model(v_in, gain=gain):
        return v_in * gain / (gain + 1)

    def run_trial(v_in, should_print=True):
        t.poke(dut.v_in, v_in)
        t.eval()
        if should_print:
            t.print('v_in: %0f, v_out: %0f\n', dut.v_in, dut.v_out)
        t.expect(dut.v_out, model(v_in), abs_tol=1e-3)

    # record tests
    run_trial(0.1)
    run_trial(0.2)
    run_trial(-0.1)
    run_trial(-0.2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('circuit_amp/test_circuit_amp.sv')],
        real_type=real_type
    )
