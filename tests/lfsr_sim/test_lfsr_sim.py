# general imports
from pathlib import Path

# AHA imports
import magma as m
from random import seed, randint

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator
from msdsl.lfsr import LFSR

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)
    seed(0)
    metafunc.parametrize('width,init', [(k, randint(0, (1<<k)-2)) for k in range(3, 10)])

def gen_model(width, init, real_type):
    # declare module
    m = MixedSignalModel('model', real_type=real_type)
    m.add_digital_input('clk')
    m.add_digital_input('rst')
    m.add_digital_output('out', width=width)

    # bind expression to internal signal
    lfsr = m.lfsr_signal(width, clk=m.clk, rst=m.rst, init=init)
    m.set_this_cycle(m.out, lfsr)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_lfsr_sim(simulator, width, init, real_type):
    # generate the SystemVerilog code
    model_file = gen_model(width=width, init=init, real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'model'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            out=m.Out(m.Bits[width])
        )

    # initialize the tester
    t = MsdslTester(dut, dut.clk)
    t.zero_inputs()
    t.poke(dut.rst, 1)
    t.step(2)
    t.poke(dut.rst, 0)

    # initialize the golden model
    lfsr = LFSR(width)
    state = init

    # check the behavior
    for i in range(2):
        for _ in range((1<<width)-1):
            t.expect(dut.out, state)
            state = lfsr.next_state(state)
            t.step(2)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file],
        real_type=real_type
    )

    # declare success
    print('OK!')
