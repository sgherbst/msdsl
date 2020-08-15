# general imports
from pathlib import Path

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def gen_model(real_type):
    # declare module
    m = MixedSignalModel('model', real_type=real_type)
    m.add_digital_input('clk')
    m.add_digital_input('rst')
    m.add_analog_output('g')

    # bind expression to internal signal
    m.add_digital_param('param_a')
    m.add_digital_param('param_b')
    m.add_digital_param('param_c', width=2, signed=True)
    m.add_digital_param('param_d', width=2, signed=True)
    m.add_real_param('param_e')
    m.add_real_param('param_f')

    # create state signals
    m.add_digital_state('sig1', init=m.param_a)
    m.add_digital_state('sig2', init=m.param_c, width=2, signed=True)
    m.add_analog_state('sig3', init=m.param_e, range_=25)

    # create main logic
    m.set_next_cycle(m.sig1, m.param_b, clk=m.clk, rst=m.rst)
    m.set_next_cycle(m.sig2, m.param_d, clk=m.clk, rst=m.rst)
    m.set_next_cycle(m.sig3, m.param_f, clk=m.clk, rst=m.rst)

    # sum signals to output
    m.set_this_cycle(m.g, m.sig1 + m.sig2 + m.sig3)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_parameters(simulator, real_type):
    model_file = gen_model(real_type=real_type)

    param_a = 0
    param_b = 1
    param_c = -2
    param_d = 1
    param_e = 1.23
    param_f = -4.56

    # declare circuit
    class dut(m.Circuit):
        name = 'test_parameters'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            g=fault.RealOut
        )

    t = MsdslTester(dut, dut.clk)

    t.zero_inputs()
    t.poke(dut.rst, 1)
    t.step(2)
    t.expect(dut.g, param_a + param_c + param_e, abs_tol=1e-3)

    t.poke(dut.rst, 0)
    t.step(2)
    t.expect(dut.g, param_b + param_d + param_f, abs_tol=1e-3)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, THIS_DIR / 'test_parameters.sv'],
        parameters={'param_a': param_a, 'param_b': param_b, 'param_c': param_c,
                    'param_d': param_d, 'param_e': param_e, 'param_f': param_f},
        real_type=real_type
    )

