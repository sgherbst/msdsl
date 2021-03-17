# general imports
from pathlib import Path
import numpy as np
from math import floor

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import VerilogGenerator
from msdsl.templates.oscillator import OscillatorModel

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def test_osc_model(simulator, real_type, dt_width=32, dt_scale=1e-18, abs_tol=0.1e-12):
    # generate model
    model = OscillatorModel(
        module_name='model',
        clk='clk',
        rst='rst',
        dt_width=dt_width,
        dt_scale=dt_scale,
        real_type=real_type,
        build_dir=BUILD_DIR,
    )
    model_file = model.compile_to_file(VerilogGenerator())

    # declare circuit
    class dut(m.Circuit):
        name = 'test_osc_model'
        io = m.IO(
            period=fault.RealIn,
            ext_dt=fault.RealIn,
            clk=m.ClockIn,
            rst=m.BitIn,
            dt_req=fault.RealOut,
            clk_en=m.BitOut
        )

    # create the tester
    tester = MsdslTester(dut, dut.clk)

    # initialize
    period = 62.5e-12
    tester.poke(dut.period, period)
    tester.poke(dut.ext_dt, 0)
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 0)
    tester.eval()

    # apply reset
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # software model of the oscillator
    def run_cycle(ext_dt, prev_state):
        # determine if the dt request is granted
        dt_req_grant = ext_dt >= prev_state
        print(f'Expecting clk_en={dt_req_grant}')

        # run the cycle
        tester.expect(dut.dt_req, prev_state, abs_tol=abs_tol)
        tester.poke(dut.ext_dt, ext_dt)
        tester.eval()
        tester.expect(dut.clk_en, dt_req_grant)
        tester.step(2)

        # return new state
        return period if dt_req_grant else prev_state-ext_dt

    # run cycles
    prev_state = period
    prev_state = run_cycle(32.1e-12, prev_state)
    prev_state = run_cycle(345e-12, prev_state)
    prev_state = run_cycle(345e-12, prev_state)
    prev_state = run_cycle(20e-12, prev_state)
    prev_state = run_cycle(20e-12, prev_state)
    prev_state = run_cycle(20e-12, prev_state)
    prev_state = run_cycle(20e-12, prev_state)
    prev_state = run_cycle(123e-12, prev_state)
    prev_state = run_cycle(12.3e-12, prev_state)
    prev_state = run_cycle(23.4e-12, prev_state)
    prev_state = run_cycle(34.5e-12, prev_state)
    prev_state = run_cycle(45.6e-12, prev_state)
    prev_state = run_cycle(56.7e-12, prev_state)
    prev_state = run_cycle(67.8e-12, prev_state)

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('osc_model/test_osc_model.sv')],
        real_type=real_type,
        defines={'DT_WIDTH': dt_width, 'DT_SCALE': dt_scale},
        #dump_waveforms=True
    )
