# general imports
from pathlib import Path
import numpy as np

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, get_msdsl_header

BUILD_DIR = Path(__file__).resolve().parent / 'build'
DOMAIN = np.pi
RANGE = 1.0

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def myfunc(x):
    # clip input
    x = np.clip(x, -DOMAIN, +DOMAIN)
    # apply function
    return np.sin(x)

def gen_model():
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR)
    model.add_analog_input('in_')
    model.add_analog_output('out')
    model.add_digital_input('clk')

    # create function
    real_func = model.make_function(myfunc, domain=[-DOMAIN, +DOMAIN])

    # apply function
    model.set_from_sync_func(model.out, real_func, model.in_, clk=model.clk)

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_func_sim(simulator):
    # generate model
    model_file = gen_model()

    # declare circuit
    class dut(m.Circuit):
        name = 'test_func_sim'
        io = m.IO(
            in_=fault.RealIn,
            out=fault.RealOut,
            clk=m.In(m.Clock)
        )

    # create the tester
    tester = fault.Tester(dut, dut.clk)

    # initialize
    tester.poke(dut.clk, 0)
    tester.poke(dut.in_, 0)
    tester.eval()

    # print the first few outputs
    for in_ in np.linspace(-1.2*DOMAIN, +1.2*DOMAIN, 100):
        tester.poke(dut.in_, in_)
        tester.step(2)
        tester.expect(dut.out, myfunc(in_), abs_tol=0.02)

    # run the simulation
    parameters = {
        'in_range': 2*DOMAIN,
        'out_range': 2*RANGE
    }
    tester.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('func_sim/test_func_sim.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        parameters=parameters,
        ext_model_file=True,
        disp_type='realtime'
    )
