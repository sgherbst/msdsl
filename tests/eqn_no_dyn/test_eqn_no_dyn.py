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

NAME = '_'.join(Path(__file__).stem.split('_')[1:])
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(const=1.23):
    # declare module
    m = MixedSignalModel('model')
    m.add_analog_input('a')
    m.add_analog_output('b')

    m.add_eqn_sys([
        m.b == const*m.a
    ])

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_eqn_no_dyn(simulator, const=1.23):
    model_file = gen_model(const=const)

    # declare circuit
    class dut(m.Circuit):
        name=f'test_{NAME}'
        io=m.IO(
            a=fault.RealIn,
            b=fault.RealOut
        )

    t = fault.Tester(dut)

    def run_trial(a, should_print=True):
        t.poke(dut.a, a)
        t.eval()
        if should_print:
            t.print('a: %0f, b: %0f\n', dut.a, dut.b)
        t.expect(dut.b, const*a, abs_tol=1e-3)

    # record tests
    run_trial(1.23)
    run_trial(-1.23)
    run_trial(2.34)
    run_trial(-2.34)

    # run the simulation
    t.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )
