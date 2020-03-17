# general imports
import numpy as np
from math import floor
from pathlib import Path

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, to_sint, clamp_op, get_msdsl_header

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(n, vn, vp, dt):
    # declare model I/O
    m = MixedSignalModel('model', dt=dt)
    m.add_analog_input('a_in')
    m.add_digital_output('d_out', width=n, signed=True)

    # compute expression for ADC output as an unclamped, real number
    expr = ((m.a_in-vn)/(vp-vn) * ((2**n)-1)) - (2**(n-1))

    # clamp to ADC range
    clamped = clamp_op(expr, -(2**(n-1)), (2**(n-1))-1)

    # assign expression to output
    m.set_this_cycle(m.d_out, to_sint(clamped, width=n))

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_adc(simulator, n_adc=8, v_ref_n=-1.0, v_ref_p=+1.0, dt=0.1e-6):
    model_file = gen_model(n=n_adc, vn=v_ref_n, vp=v_ref_p, dt=dt)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_adc'
        io = m.IO(
            a_in=fault.RealIn,
            d_out=m.Out(m.SInt[n_adc])
        )

    def model(a_in):
        code = ((a_in - v_ref_n) / (v_ref_p - v_ref_n)) * ((2**n_adc) - 1)
        code -= 2**(n_adc - 1)
        code = min(max(code, -(2**(n_adc-1))), (2**(n_adc-1))-1)
        code = floor(code)
        return code

    # create mechanism to run trials
    t = fault.Tester(dut, expect_strict_default=True)
    def run_trial(a_in, should_print=False):
        t.poke(dut.a_in, a_in)
        t.eval()
        if should_print:
            t.print('a_in: %0f, d_out: %0d\n', dut.a_in, dut.d_out)
        t.expect(dut.d_out, model(a_in))

    # specify trials to be run
    delta = 0.1*(v_ref_p - v_ref_n)
    for x in np.linspace(v_ref_n - delta, v_ref_p + delta, 1000):
        run_trial(x)

    # run the simulation
    t.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('adc/test_adc.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        parameters={'n_adc': n_adc},
        ext_model_file=True,
        disp_type='realtime'
    )
