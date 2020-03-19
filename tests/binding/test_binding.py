# general imports
from pathlib import Path

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, get_msdsl_header

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model():
    # declare module
    m = MixedSignalModel('model')
    m.add_analog_input('a')
    m.add_analog_input('b')

    # bind expression to internal signal
    m.bind_name('c', m.a + m.b)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_binding(simulator):
    model_file = gen_model()

    # declare circuit
    class dut(m.Circuit):
        name = 'test_binding'
        io = m.IO(
            a=fault.RealIn,
            b=fault.RealIn,
            c=fault.RealOut
        )

    t = fault.Tester(dut)

    def run_trial(a, b, should_print=True):
        t.poke(dut.a, a)
        t.poke(dut.b, b)
        t.eval()
        if should_print:
            t.print('a: %0f, b: %0f, c: %0f\n', dut.a, dut.b, dut.c)
        t.expect(dut.c, a+b, abs_tol=1e-3)

    # record tests
    run_trial(1.23, 2.34)
    run_trial(-3.45, 4.56)
    run_trial(5.67, -7.89)

    # run the simulation
    t.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('binding/test_binding.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )
