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

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)

def gen_model(real_vals, sint_vals, uint_vals, addr_bits, sint_bits, uint_bits):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR)
    model.add_digital_input('addr', width=addr_bits)
    model.add_digital_input('clk')
    model.add_analog_output('real_out')
    model.add_digital_output('sint_out', width=sint_bits)
    model.add_digital_output('uint_out', width=uint_bits)

    # create tables
    real_table = model.make_real_table(real_vals)
    sint_table = model.make_sint_table(sint_vals)
    uint_table = model.make_uint_table(uint_vals)

    # assign values
    model.set_from_sync_rom(model.real_out, real_table, model.addr, clk=model.clk)
    model.set_from_sync_rom(model.sint_out, sint_table, model.addr, clk=model.clk)
    model.set_from_sync_rom(model.uint_out, uint_table, model.addr, clk=model.clk)

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_table_sim(simulator, addr_bits=8, real_range=10, sint_bits=8, uint_bits=8):
    # generate random data to go into the table
    n_samp = 1<<addr_bits
    real_vals = np.random.uniform(-real_range, +real_range, n_samp)
    sint_vals = np.random.randint(-(1<<(sint_bits-1)), 1<<(sint_bits-1), n_samp)
    uint_vals = np.random.randint(0, 1<<uint_bits, n_samp)

    # generate model
    model_file = gen_model(real_vals, sint_vals, uint_vals, addr_bits, sint_bits, uint_bits)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_table_sim'
        io = m.IO(
            addr=m.In(m.Bits[addr_bits]),
            clk=m.In(m.Clock),
            real_out=fault.RealOut,
            sint_out=m.Out(m.SInt[sint_bits]),
            uint_out=m.Out(m.UInt[uint_bits])
        )

    # create the tester
    tester = fault.Tester(dut, dut.clk)

    # initialize
    tester.poke(dut.clk, 0)
    tester.poke(dut.addr, 0)
    tester.eval()

    # print the first few outputs
    for k, (real_val, sint_val, uint_val) \
            in enumerate(zip(real_vals, sint_vals, uint_vals)):
        tester.poke(dut.addr, k)
        tester.step(2)
        tester.expect(dut.real_out, real_val, abs_tol=0.001)
        tester.expect(dut.sint_out, int(sint_val))
        tester.expect(dut.uint_out, int(uint_val))

    # run the simulation
    parameters = {
        'addr_bits': addr_bits,
        'real_range': real_range,
        'sint_bits': sint_bits,
        'uint_bits': uint_bits
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
