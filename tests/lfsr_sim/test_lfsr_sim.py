# general imports
from pathlib import Path

# AHA imports
import magma as m
import fault
from random import seed, randint

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params
from msdsl import MixedSignalModel, VerilogGenerator, get_msdsl_header
from msdsl.lfsr import LFSR

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    seed(0)
    metafunc.parametrize('width,init', [(k, randint(0, (1<<k)-2)) for k in range(3, 10)])

def gen_model(width, init):
    # declare module
    m = MixedSignalModel('model')
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

def test_lfsr_sim(simulator, width, init):
    # generate the SystemVerilog code
    model_file = gen_model(width=width, init=init)

    # declare circuit
    class dut(m.Circuit):
        name = 'model'
        io = m.IO(
            clk=m.ClockIn,
            rst=m.BitIn,
            out=m.Out(m.Bits[width])
        )

    # initialize the tester
    t = fault.Tester(dut, dut.clk)
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
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        ext_model_file=True,
        disp_type='realtime'
    )

    # declare success
    print('OK!')