# general imports
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, eqn_case, Deriv

NAME = Path(__file__).stem.split('_')[1]
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(tau_f=1e-9, tau_s=100e-9, dt=10e-9, real_type=RealType.FixedPoint):
    m = MixedSignalModel('model', dt=dt, real_type=real_type)
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

def test_det(simulator, real_type, tau_f=1e-9, tau_s=100e-9, dt=10e-9):
    model_file = gen_model(tau_f=tau_f, tau_s=tau_s, dt=dt, real_type=real_type)

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

    def debug():
        tester.print("v_in: %0f, v_out: %0f\n", dut.v_in, dut.v_out)

    # initialize
    v_in = 0.0
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.poke(dut.v_in, v_in)
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # check initial values
    debug()
    tester.expect(dut.v_out, 0.0, abs_tol=1e-3)

    # poke input
    tester.poke(dut.v_in, 1.5)
    tester.step(2)
    debug()
    tester.expect(dut.v_out, 1.5, abs_tol=0.1)

    # clear input and make sure output is still high
    tester.poke(dut.v_in, 0.0)
    tester.step(2)
    debug()
    tester.expect(dut.v_out, 1.4, abs_tol=0.1)

    # wait longer for output to decay back to zero
    tester.step(2*30)
    debug()
    tester.expect(dut.v_out, 0.0, abs_tol=0.1)

    # poke input again
    tester.poke(dut.v_in, 1.5)
    tester.step(2)
    debug()
    tester.expect(dut.v_out, 1.5, abs_tol=0.1)

    # this time set input to a mid-range value
    tester.poke(dut.v_in, 0.5)
    tester.step(2)
    debug()
    tester.expect(dut.v_out, 1.4, abs_tol=0.1)

    # wait longer for output to decay to new input
    tester.step(2*30)
    debug()
    tester.expect(dut.v_out, 0.5, abs_tol=0.1)

    # increase input and make sure output tracks immediately
    tester.poke(dut.v_in, 2.5)
    tester.step(2)
    debug()
    tester.expect(dut.v_out, 2.5, abs_tol=0.1)

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        real_type=real_type
    )
