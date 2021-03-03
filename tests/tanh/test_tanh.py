# general imports
from pathlib import Path
import numpy as np

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator
from msdsl.interp.nonlin import calc_tanh_vsat, tanhsat

BUILD_DIR = Path(__file__).resolve().parent / 'build'
VSAT = calc_tanh_vsat(-1, 'dB')

def myfunc(v):
    return tanhsat(v, VSAT)

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(order=1, numel=64, real_type=RealType.FixedPoint):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR, real_type=real_type)
    model.add_analog_input('in_')
    model.add_analog_output('out')

    # create function
    real_func = model.make_function(myfunc, domain=[-2.0, +2.0], order=order, numel=numel, write_tables=False)

    # apply function
    model.set_from_func(model.out, real_func, model.in_, func_mode='async')

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_tanh(simulator, real_type, err_lim=2.5e-4):
    # set the random seed for repeatable results
    np.random.seed(0)

    # generate model
    model_file = gen_model(real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_tanh'
        io = m.IO(
            in_=fault.RealIn,
            out=fault.RealOut
        )

    # create the tester
    tester = MsdslTester(dut)

    # initialize
    tester.poke(dut.in_, 0)
    tester.eval()

    # save the outputs
    inpts = np.random.uniform(-2, +2, 100)
    apprx = []
    for in_ in inpts:
        tester.poke(dut.in_, in_)
        tester.eval()
        apprx.append(tester.get_value(dut.out))

    # run the simulation
    parameters = {
        'in_range': 2.5,
        'out_range': 2.5
    }
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('tanh/test_tanh.sv')],
        parameters=parameters,
        real_type=real_type
    )

    # evaluate the outputs
    apprx = np.array([elem.value for elem in apprx], dtype=float)

    # compute the exact response to inputs
    exact = myfunc(inpts)

    # check the result
    err = np.sqrt(np.mean((exact-apprx)**2))
    print(f'RMS error: {err}')
    assert err <= err_lim
