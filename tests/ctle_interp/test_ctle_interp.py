# general imports
from pathlib import Path
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import lfilter, cont2discrete

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import VerilogGenerator
from msdsl.templates.lds import CTLEModel
from msdsl.interp.ctle import calc_ctle_num_den

BUILD_DIR = Path(__file__).resolve().parent / 'build'
NPTS = 4

def make_cubic_func(*args):
    # define equations
    A = np.zeros((4, 4), dtype=float)
    for k in range(4):
        pt = k/3
        A[k, :] = [1, pt, pt**2, pt**3]

    # solve equation
    b = np.array(args)
    x = np.linalg.solve(A, b)

    # define function
    def retval(t):
        return x[0]+(x[1]*t)+(x[2]*(t**2))+(x[3]*(t**3))

    # return result
    return retval

def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc)

def test_ctle_interp(simulator, real_type, fz=0.8e9, fp1=1.6e9, gbw=40e9,
                     dtmax=62.5e-12, nover=2500000, n_segs=25, err_lim=5e-4):
    # make sure test is repeatable
    # the seed is chosen to make sure the curve is interesting enough
    np.random.seed(4)

    # generate model
    model = CTLEModel(fz=fz, fp1=fp1, gbw=gbw, dtmax=dtmax, module_name='model',
                      build_dir=BUILD_DIR, clk='clk', rst='rst',
                      real_type=real_type)
    model_file = model.compile_to_file(VerilogGenerator())

    # create IO dictionary
    ios = {}
    for k in range(NPTS):
        ios[f'in_{k}'] = fault.RealIn
        ios[f'out_{k}'] = fault.RealOut

    # declare circuit
    class dut(m.Circuit):
        name = 'test_ctle_interp'
        io = m.IO(
            dt=fault.RealIn,
            clk=m.In(m.Clock),
            rst=m.BitIn,
            **ios
        )

    # create the tester
    tester = MsdslTester(dut, dut.clk)

    # convenience functions for reading/writing splines
    def poke_input_spline(vals):
        for k in range(NPTS):
            tester.poke(getattr(dut, f'in_{k}'), vals[k])
    def get_output_spline():
        retval = []
        for k in range(NPTS):
            retval.append(tester.get_value(getattr(dut, f'out_{k}')))
        return retval

    # define input segments
    min_v, max_v = -2, +2
    widths = np.random.uniform(0, 1, n_segs)
    times = np.concatenate(([0], np.cumsum(widths)))
    segs = [np.random.uniform(min_v, max_v, NPTS)]
    for k in range(1, n_segs):
        prv = make_cubic_func(*segs[k-1])(widths[k-1])
        nxt = np.random.uniform(min_v, max_v, NPTS-1)
        segs.append(np.concatenate(([prv], nxt)))

    # initialize
    poke_input_spline([0]*NPTS)
    tester.poke(dut.dt, 0)
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.eval()

    # apply reset
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # apply segments
    meas = []
    for k in range(n_segs):
        poke_input_spline(segs[k])
        tester.poke(dut.dt, widths[k])
        tester.eval()
        meas.append(get_output_spline())
        tester.step(2)

    # run the simulation
    parameters = {
        'in_range': 4.5,
        'out_range': 4.5
    }
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('ctle_interp/test_ctle_interp.sv')],
        parameters=parameters,
        real_type=real_type,
        #dump_waveforms=True
    )

    # convert measurements to arrays
    meas = [np.array([pt.value for pt in seg]) for seg in meas]

    # create oversampled time vector and split into chunks corresponding to each cubic section
    tvec = np.linspace(0, times[-1], nover)
    ivec = [np.searchsorted(tvec, time) for time in times[1:-1]]
    tvec = np.split(tvec, ivec)

    # create a flat vector of input values
    xvec = [make_cubic_func(*segs[k])(tvec[k]-times[k]) for k in range(n_segs)]
    xvec = np.concatenate(xvec)

    # apply CTLE dynamics to flat input vector, then split output values into chunks
    # corresponding to each cubic section
    num, den = calc_ctle_num_den(fz=fz*dtmax, fp1=fp1*dtmax, gbw=gbw*dtmax)
    b, a, _ = cont2discrete((num, den), dt=times[-1]/(nover-1))
    yvec = lfilter(b[0], a, xvec)
    yvec = np.split(yvec, ivec)

    # evaluate the error for the chunk corresponding to each cubic section
    errs = []
    for k in range(n_segs):
        svec = np.arange(0, widths[k], 1/(NPTS-1))
        expt = interp1d(tvec[k]-times[k], yvec[k], bounds_error=False, fill_value='extrapolate')(svec)
        errs.append(meas[k][:len(expt)]-expt)

    # compute maximum error
    max_err = max([np.max(np.abs(elem)) for elem in errs])
    print(f'max_err: {max_err}')

    # make sure the worst-case error is within tolerance
    assert max_err < err_lim
