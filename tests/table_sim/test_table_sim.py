# general imports
from pathlib import Path
import numpy as np
from math import ceil, log2

# AHA imports
import magma as m
import fault

# svreal import
from svreal import get_svreal_header

# msdsl imports
from ..common import pytest_sim_params, get_file
from msdsl import MixedSignalModel, VerilogGenerator, get_msdsl_header
from msdsl.expr.table import RealTable

BUILD_DIR = Path(__file__).resolve().parent / 'build'

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(real_vals):
    # create mixed-signal model
    model = MixedSignalModel('model')
    model.add_digital_input('addr', width=int(ceil(log2(len(real_vals)))))
    model.add_digital_input('clk')
    model.add_analog_output('out')

    # write tables
    table = RealTable(real_vals, dir=BUILD_DIR)
    table.to_file()

    # assign value
    model.set_from_sync_rom(model.out, table, model.addr, clk=model.clk)

    # write the model
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    model_file = BUILD_DIR / 'model.sv'
    model.compile_to_file(VerilogGenerator(), filename=model_file)

    # return the location of the model
    return model_file

def test_table_sim(simulator, addr_bits=10, out_range=10):
    # generate random data to go into the table
    real_vals = np.random.uniform(-out_range, +out_range, 1<<addr_bits)

    # generate model
    model_file = gen_model(real_vals)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_table_sim'
        io = m.IO(
            addr=m.In(m.Bits[addr_bits]),
            clk=m.In(m.Clock),
            out=fault.RealOut
        )

    # create the tester
    tester = fault.Tester(dut, dut.clk)

    # initialize
    tester.poke(dut.clk, 0)
    tester.poke(dut.addr, 0)
    tester.eval()

    # print the first few outputs
    for k, val in enumerate(real_vals):
        tester.poke(dut.addr, k)
        tester.step(2)
        tester.expect(dut.out, val, abs_tol=0.001)

    # run the simulation
    parameters = {
        'addr_bits': addr_bits,
        'out_range': out_range
    }
    tester.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('table_sim/test_table_sim.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        parameters=parameters,
        ext_model_file=True,
        disp_type='realtime'
    )
