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
                     dtmax=62.5e-12, nover=100000, err_lim=1e-4):
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
    seg1 = [-2, 0, -0.25, 1.75]
    seg2 = [1.75, 0, 0.1, -0.3]
    seg3 = [-0.3, -0.1, -0.1, 1.25]

    # initialize
    poke_input_spline([0]*NPTS)
    tester.poke(dut.dt, 1.0)
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.eval()

    # apply reset
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # segment 1
    poke_input_spline(seg1)
    tester.eval()
    y1_meas = get_output_spline()
    tester.step(2)

    # segment 2
    poke_input_spline(seg2)
    tester.eval()
    y2_meas = get_output_spline()
    tester.step(2)

    # segment 3
    poke_input_spline(seg3)
    tester.eval()
    y3_meas = get_output_spline()
    tester.step(2)

    # run the simulation
    parameters = {
        'in_range': 3.5,
        'out_range': 3.5
    }
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('ctle_interp/test_ctle_interp.sv')],
        parameters=parameters,
        real_type=real_type
    )

    # convert measurements to arrays
    y1_meas = np.array([elem.value for elem in y1_meas])
    y2_meas = np.array([elem.value for elem in y2_meas])
    y3_meas = np.array([elem.value for elem in y3_meas])

    # calculate response using conventional method
    num, den = calc_ctle_num_den(fz=fz*dtmax, fp1=fp1*dtmax, gbw=gbw*dtmax)
    tvec = np.linspace(0, 1, nover)
    xvec = np.concatenate((
        make_cubic_func(*seg1)(tvec[:-1]),
        make_cubic_func(*seg2)(tvec[:-1]),
        make_cubic_func(*seg3)(tvec)
    ))
    b, a, _ = cont2discrete((num, den), dt=1/(nover-1))
    y_expt = lfilter(b[0], a, xvec)

    # check the output a certain specific points
    y1_expt = y_expt[(0*(nover-1)):((1*nover)-0)]
    y2_expt = y_expt[(1*(nover-1)):((2*nover)-1)]
    y3_expt = y_expt[(2*(nover-1)):((3*nover)-2)]

    # sanity check to make sure slices are OK
    assert len(y1_expt) == nover
    assert len(y2_expt) == nover
    assert len(y3_expt) == nover

    # sample output of conventional method
    svec = np.linspace(0, 1, NPTS)
    y1_expt_i = interp1d(tvec, y1_expt)(svec)
    y2_expt_i = interp1d(tvec, y2_expt)(svec)
    y3_expt_i = interp1d(tvec, y3_expt)(svec)

    # run comparisons
    assert np.max(np.abs(y1_meas - y1_expt_i)) < err_lim
    assert np.max(np.abs(y2_meas - y2_expt_i)) < err_lim
    assert np.max(np.abs(y3_meas - y3_expt_i)) < err_lim
