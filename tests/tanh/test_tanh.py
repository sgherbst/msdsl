# general imports
from pathlib import Path
import numpy as np

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import VerilogGenerator
from msdsl.templates.saturation import SaturationModel

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def test_tanh(simulator, real_type, err_lim=2.5e-4):
    # set the random seed for repeatable results
    np.random.seed(0)

    # generate model
    model = SaturationModel('model', build_dir=BUILD_DIR, real_type=real_type)
    model_file = model.compile_to_file(VerilogGenerator())

    # declare circuit
    class dut(m.Circuit):
        name = 'test_tanh'
        io = m.IO(
            in_=fault.RealIn,
            out=fault.RealOut
        )

    # create the tester
    tester = MsdslTester(dut)

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
    exact = model.func(inpts)

    # check the result
    err = np.sqrt(np.mean((exact-apprx)**2))
    print(f'RMS error: {err}')
    assert err <= err_lim
