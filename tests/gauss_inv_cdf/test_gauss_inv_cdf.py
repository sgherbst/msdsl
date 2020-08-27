# general imports
from pathlib import Path
import numpy as np
import numpy.ma as ma
from scipy.stats import truncnorm

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import MixedSignalModel, VerilogGenerator, compress_uint

BUILD_DIR = Path(__file__).resolve().parent / 'build'
N_BITS = 31

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

# inverse CDF
def inv_cdf(x):
    return truncnorm.ppf(x, -8, 8)

# logarithmic mapping
def map_f(r):
    # convert input to an array
    # ref: https://stackoverflow.com/questions/29318459/python-function-that-handles-scalar-or-arrays
    r = np.asarray(r)
    scalar_input = False
    if r.ndim == 0:
        r = r[np.newaxis]  # make 1D
        scalar_input = True

    # compute x and y values
    x = np.floor(ma.log2(r)) + 1.0
    y = (r/(2.0**(x-1.0))) - 1.0

    # compute the sum of x and y, filling zero
    # where there are masked values (should only
    # occur when there are zero entries)
    retval = (x + y).filled(0)

    # return scalar or array
    if scalar_input:
        return np.squeeze(retval)
    else:
        return retval

def unmap_f(r):
    # convert input to an array
    # ref: https://stackoverflow.com/questions/29318459/python-function-that-handles-scalar-or-arrays
    r = np.asarray(r)
    scalar_input = False
    if r.ndim == 0:
        r = r[np.newaxis]  # make 1D
        scalar_input = True

    # invert the mapping
    x = np.floor(r)
    retval = (2.0**(x-1)) * (1 + r - x)

    # make sure zero maps to zero
    retval[r==0] = 0

    # return scalar or array
    if scalar_input:
        return np.squeeze(retval)
    else:
        return retval

def gen_model(real_type):
    # create mixed-signal model
    model = MixedSignalModel('model', build_dir=BUILD_DIR,
                             real_type=real_type)
    model.add_digital_input('in_', width=N_BITS)
    model.add_analog_output('out')
    model.add_digital_input('clk')
    model.add_digital_input('rst')

    # create function
    domain = [map_f(0), map_f((1<<N_BITS) - 1)]
    real_func = model.make_function(
        lambda x: inv_cdf(unmap_f(x)/(1<<(N_BITS+1))),
        domain=domain,
        order=1,
        numel=512
    )

    # apply function
    mapped = compress_uint(model.in_)
    model.set_from_sync_func(model.out, real_func, mapped, clk=model.clk, rst=model.rst)

    # write the model
    return model.compile_to_file(VerilogGenerator())

def test_gauss_inv_cdf(simulator, real_type, err_lim=0.005):
    # set the random seed for repeatable results
    np.random.seed(0)

    # generate model
    model_file = gen_model(real_type=real_type)

    # declare circuit
    class dut(m.Circuit):
        name = 'test_gauss_inv_cdf'
        io = m.IO(
            in_=m.In(m.Bits[31]),
            out=fault.RealOut,
            clk=m.In(m.Clock),
            rst=m.BitIn
        )

    # create the tester
    t = MsdslTester(dut, dut.clk)

    # initialize
    t.zero_inputs()
    t.poke(dut.rst, 1)
    t.step(2)

    # clear reset
    t.poke(dut.rst, 0)
    t.step(2)

    # determine input values
    inpts = []

    # specifically-chosen entries
    for k in range(0, N_BITS-1):
        inpts.append((1<<k)-1)
        inpts.append((1<<k)+0)
        inpts.append((1<<k)+1)
    inpts.append((1<<(N_BITS-1))-1)
    inpts.append(1<<(N_BITS-1))

    # pseudo-random entries chosen in a logarithmic fashion
    # the random seed is chosen to make sure this test has
    # consistent result in regression testing
    rand_pts = 2**(np.random.uniform(0, N_BITS, 100))
    rand_pts = np.floor(rand_pts).astype(np.int)
    rand_pts = [int(elem) for elem in rand_pts]
    inpts += rand_pts

    # sort input
    inpts = np.sort(inpts)

    meas = []
    for in_ in inpts:
        t.poke(dut.in_, int(in_))
        t.step(2)
        meas.append(t.get_value(dut.out))

    # run the simulation
    t.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('gauss_inv_cdf/test_gauss_inv_cdf.sv')],
        real_type=real_type
    )

    # evaluate the outputs
    meas = np.array([elem.value for elem in meas], dtype=float)

    # compute the exact response to inputs
    expct = inv_cdf(inpts/(1<<(N_BITS+1)))

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.semilogx(inpts[1:], meas[1:])
    # plt.semilogx(inpts[1:], expct[1:])
    # plt.legend(['meas', 'expct'])
    # plt.show()

    # print the maximum error
    err = meas - expct
    idx = np.argmax(np.abs(err))
    print(f'Largest error: {err[idx]} @ {inpts[idx]}')

    # check that the maximum error is within limits
    assert err[idx] <= err_lim, 'Error out of tolerance'
