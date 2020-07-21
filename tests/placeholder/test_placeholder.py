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
from msdsl.function import PlaceholderFunction

BUILD_DIR = Path(__file__).resolve().parent / 'build'
DOMAIN = np.pi
RANGE = 1.0
COEFF_EXPS = [-16, -20]

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    tests = [(0, 0.0105, 9, 18),
             (1, 0.000318, 7, 18)]
    metafunc.parametrize('order,err_lim,addr_bits,data_bits', tests)

def clip_sin(x):
    # clip input
    x = np.clip(x, -DOMAIN, +DOMAIN)
    # apply function
    return np.sin(x)

def clip_cos(x):
    # clip input
    x = np.clip(x, -DOMAIN, +DOMAIN)
    # apply function
    return np.cos(x)

def gen_model(placeholder, addr_bits=9, data_bits=18):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR)
    model.add_analog_input('in_')
    model.add_analog_output('out')
    model.add_digital_input('clk')
    model.add_digital_input('rst')
    model.add_digital_input('wdata0', width=data_bits, signed=True)
    model.add_digital_input('wdata1', width=data_bits, signed=True)
    model.add_digital_input('waddr', width=addr_bits)
    model.add_digital_input('we')

    # apply function
    model.set_from_sync_func(model.out, placeholder, model.in_, clk=model.clk, rst=model.rst,
                             wdata=[model.wdata0, model.wdata1], waddr=model.waddr, we=model.we)

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_placeholder(simulator, order, err_lim, addr_bits, data_bits):
    # set the random seed for repeatable results
    np.random.seed(0)

    # generate model
    placeholder = PlaceholderFunction(domain=[-DOMAIN, +DOMAIN], order=order,
                                      numel=1<<addr_bits, coeff_widths=[data_bits]*(order+1),
                                      coeff_exps=COEFF_EXPS[:(order+1)])
    model_file = gen_model(placeholder=placeholder, addr_bits=addr_bits, data_bits=data_bits)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_placeholder'
        io = m.IO(
            in_=fault.RealIn,
            out=fault.RealOut,
            clk=m.In(m.Clock),
            rst=m.BitIn,
            wdata0=m.In(m.Bits[data_bits]),
            wdata1=m.In(m.Bits[data_bits]),
            waddr=m.In(m.Bits[addr_bits]),
            we=m.BitIn
        )

    # create the tester
    t = fault.Tester(dut, dut.clk)

    # initialize
    t.zero_inputs()
    t.poke(dut.rst, 1)
    t.step(2)

    # clear reset
    t.poke(dut.rst, 0)
    t.step(2)

    # define a method for testing out the placeholder feature
    # with an arbitrary function
    def run_trial(func):
        # determine coefficients for order=0 and order=1
        coeffs_bin = placeholder.get_coeffs_bin_fmt(func)

        # write coefficients
        t.poke(dut.we, 1)
        for i in range(1<<addr_bits):
            if order >= 0:
                t.poke(dut.wdata0, coeffs_bin[0][i])
            if order >= 1:
                t.poke(dut.wdata1, coeffs_bin[1][i])
            if order >= 2:
                raise Exception('Only order=0 and order=1 are implemented for this test.')
            t.poke(dut.waddr, i)
            t.step(2)
        t.poke(dut.we, 0)

        # save the outputs
        inpts = np.random.uniform(-1.2*DOMAIN, +1.2*DOMAIN, 100)
        apprx = []
        for in_ in inpts:
            t.poke(dut.in_, in_)
            t.step(2)
            apprx.append(t.get_value(dut.out))

        # return the list of saved outputs
        return inpts, apprx

    # actually run the trials, using "sine" and "cosine"
    inpts0, apprx0 = run_trial(clip_sin)
    inpts1, apprx1 = run_trial(clip_cos)

    # define simulation parameters
    parameters = {
        'in_range': 2*DOMAIN,
        'out_range': 2*RANGE,
        'addr_bits': addr_bits,
        'data_bits': data_bits
    }

    # run the simulation
    t.compile_and_run(
        target='system-verilog',
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('placeholder/test_placeholder.sv')],
        inc_dirs=[get_svreal_header().parent, get_msdsl_header().parent],
        parameters=parameters,
        ext_model_file=True,
        disp_type='realtime'
    )

    # evaluate the outputs
    apprx0 = np.array([elem.value for elem in apprx0], dtype=float)
    apprx1 = np.array([elem.value for elem in apprx1], dtype=float)

    # compute the exact response to inputs
    exact0 = clip_sin(inpts0)
    exact1 = clip_cos(inpts1)

    # calculate errors
    err0 = np.sqrt(np.mean((exact0-apprx0)**2))
    err1 = np.sqrt(np.mean((exact1-apprx1)**2))
    print(f'err0: {err0}')
    print(f'err1: {err1}')

    # check the result
    assert err0 <= err_lim, 'err0 is out of spec'
    assert err1 <= err_lim, 'err1 is out of spec'
