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

def gen_model():
    # declare model I/O
    m = MixedSignalModel('model')
    m.add_digital_input('a', width=63, signed=True)
    m.add_digital_input('b', width=63, signed=True)
    m.add_digital_output('c', width=64, signed=True)

    # assign expression to output
    m.bind_name('d', m.a - m.b)
    m.set_this_cycle(m.c, m.d)

    # compile to a file
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    m.compile_to_file(VerilogGenerator(), filename=model_file)

    # return file location
    return model_file

def test_sub(simulator):
    model_file = gen_model()

    # declare circuit
    class dut(m.Circuit):
        name = 'test_sub'
        io = m.IO(
            a=m.In(m.SInt[63]),
            b=m.In(m.SInt[63]),
            c=m.Out(m.SInt[64])
        )

    def model(a, b):
        return a - b

    # create mechanism to run trials
    t = MsdslTester(dut)
    def run_trial(a, b, should_print=False):
        t.poke(dut.a, a)
        t.poke(dut.b, b)
        t.eval()
        if should_print:
            t.print('a: %0d, b: %0d, c: %0d\n', dut.a, dut.b, dut.c)
        t.expect(dut.c, model(a, b))

    # determine tolerance
    run_trial(1293371963190904369, 4127252734515468513)
    run_trial(4401526010147921985, -2843975463655034865)
    run_trial(3334474569623275707, -2203503052900441272)
    run_trial(-2576643849353512883, -2271681343036037956)
    run_trial(1562136255888534365, 1335463821191115164)

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('sub/test_sub.sv')]
    )
