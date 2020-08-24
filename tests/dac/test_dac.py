# general imports
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(n, vn, vp, dt, real_type):
    # declare model I/O
    m = MixedSignalModel('model', dt=dt, real_type=real_type)
    m.add_digital_input('d_in', width=n, signed=True)
    m.add_analog_output('a_out')

    # compute expression for DAC output
    expr = ((m.d_in + (2**(n-1)))/((2**n)-1))*(vp-vn) + vn

    # assign expression to output
    m.set_this_cycle(m.a_out, expr)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_adc(simulator, real_type, n_dac=8, v_ref_n=-1.0,
             v_ref_p=+1.0, dt=0.1e-6):
    model_file = gen_model(n=n_dac, vn=v_ref_n, vp=v_ref_p,
                           dt=dt, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_dac'
        io = m.IO(
            d_in=m.In(m.SInt[n_dac]),
            a_out=fault.RealOut
        )

    def model(d_in):
        # scale code to real number from 0 to 1
        out = (d_in + (2**(n_dac-1))) / ((2**n_dac)-1)

        # apply scaling and offset
        out *= (v_ref_p - v_ref_n)
        out += v_ref_n

        # return output
        return out

    # create mechanism to run trials
    t = MsdslTester(dut)
    def run_trial(d_in, should_print=False):
        t.poke(dut.d_in, d_in)
        t.eval()
        if should_print:
            t.print('d_in: %0d, a_out: %0f\n', dut.d_in, dut.a_out)
        t.expect(dut.a_out, model(d_in), abs_tol=1e-3)

    # determine tolerance
    for k in range(-(2**(n_dac-1)), (2**(n_dac-1)) - 1):
        run_trial(k)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('dac/test_dac.sv')],
        parameters={'n_dac': n_dac},
        real_type=real_type
    )
