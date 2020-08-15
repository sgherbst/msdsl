# general imports
from math import exp, cos, sin, sqrt
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, AnalogSignal, Deriv

NAME = Path(__file__).stem.split('_')[1]
BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(cap=0.16e-6, ind=0.16e-6, res=0.1, dt=0.01e-6,
              real_type=RealType.FixedPoint):
    # declare model
    m = MixedSignalModel('model', dt=dt, real_type=real_type)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('clk')
    m.add_digital_input('rst')

    # declare system of equations
    m.add_analog_state('i_ind', 10) # TODO: can this be tightened down a bit?
    v_l = AnalogSignal('v_l')
    v_r = AnalogSignal('v_r')
    eqns = [
        Deriv(m.i_ind) == v_l / ind,
        Deriv(m.v_out) == m.i_ind / cap,
        v_r == m.i_ind * res,
        m.v_in == m.v_out + v_l + v_r
    ]
    m.add_eqn_sys(eqns, clk=m.clk, rst=m.rst)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    return model_file

def test_rlc(simulator, real_type, cap=0.16e-6, ind=0.16e-6, res=0.1, dt=0.01e-6):
    model_file = gen_model(cap=cap, ind=ind, res=res, dt=dt,
                           real_type=real_type)

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

    # initialize
    v_in = 1.0
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.poke(dut.v_in, v_in)
    tester.eval()

    # reset
    tester.step(2)

    # model for circuit behavior
    # see slide 15 here: http://tuttle.merc.iastate.edu/ee201/topics/capacitors_inductors/RLC_transients.pdf
    vf = v_in
    vi = 0.0
    o = -res/(2*ind)
    wd = sqrt(1/(ind*cap)-((res/(2*ind))**2))
    def model(t):
        return vf - (vf-vi)*(exp(o*t)*(cos(wd*t)-(o/wd)*sin(wd*t)))

    # print the first few outputs
    tester.poke(dut.rst, 0)
    for k in range(20):
        tester.expect(dut.v_out, model(k*dt), abs_tol=0.025)
        tester.print("v_out: %0f\n", dut.v_out)
        tester.step(2)

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file(f'{NAME}/test_{NAME}.sv')],
        real_type=real_type
    )
