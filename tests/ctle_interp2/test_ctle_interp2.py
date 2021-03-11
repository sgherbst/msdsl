# general imports
import pytest
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d
from scipy.signal import lfilter
from scipy.signal import cont2discrete

# AHA imports
import magma as m

# msdsl imports
from ..common import *
from msdsl import VerilogGenerator
from msdsl.templates.lds import CTLEModel
from msdsl.interp.ctle import calc_ctle_num_den
from msdsl.interp.interp import calc_piecewise_poly, eval_piecewise_poly

THIS_DIR = Path(__file__).resolve().parent
BUILD_DIR = THIS_DIR / 'build'
TOP_DIR = THIS_DIR.parent.parent
DATA_FILE = TOP_DIR / 'channel_resp_mar11.csv'

def interp_emu_res(tvec, vvec, dtmax, tsim, order, npts):
    # hold the previous stop index
    stop_idx = -1
    # calculate spacing between "hidden" timesteps
    th = dtmax/(npts-1)
    # build up partial results
    results = []
    for k in range(len(tvec)):
        # find start index
        start_idx = stop_idx+1
        # find stop index
        if k == len(tvec)-1:
            stop_idx = len(tsim)-1
        else:
            stop_idx = np.searchsorted(tsim, tvec[k+1], side='left')
        # find vector of times for interpolation
        t_interp = tsim[start_idx:(stop_idx+1)] - tvec[k]
        # calculate piecewise polynomial representation
        U = calc_piecewise_poly(vvec[k], order=order)
        results.append(eval_piecewise_poly(t_interp, th, U))
    # return array of the results
    return np.concatenate(results)


def pytest_generate_tests(metafunc):
    pytest_sim_params(metafunc)
    pytest_real_type_params(metafunc, [RealType.FixedPoint])


@pytest.mark.parametrize('fz,fp1,npts,order,gbw,dtmax,err_lim', [
    (0.8e9, 1.6e9, 4, 3, 40e9, 31.25e-12, 5e-3),
])
def test_ctle_interp2(fz, fp1, npts, order, gbw, dtmax, err_lim, simulator, real_type):
    # read in data
    my_data = np.genfromtxt(DATA_FILE, delimiter=',', skip_header=1)
    t_resp = my_data[:, 1] - my_data[0, 1]
    v_resp = my_data[:, 2]

    # find timestep of oversampled data
    tover = np.median(np.diff(t_resp))
    assert np.all(np.isclose(np.diff(t_resp), tover))
    print(f'tover: {tover*1e12:0.3f} ps')

    # build interpolator for input data
    my_interp = interp1d(t_resp, v_resp)
    svec = np.linspace(0, 1, npts)

    # generate model
    model = CTLEModel(fz=fz, fp1=fp1, gbw=gbw, dtmax=dtmax, module_name='model',
                      build_dir=BUILD_DIR, clk='clk', rst='rst', real_type=real_type)
    model_file = model.compile_to_file(VerilogGenerator())

    # create IO dictionary
    ios = {}
    for k in range(npts):
        ios[f'in_{k}'] = fault.RealIn
        ios[f'out_{k}'] = fault.RealOut

    # declare circuit
    class dut(m.Circuit):
        name = 'test_ctle_interp2'
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
        for k in range(npts):
            tester.poke(getattr(dut, f'in_{k}'), vals[k])
    def get_output_spline():
        retval = []
        for k in range(npts):
            retval.append(tester.get_value(getattr(dut, f'out_{k}')))
        return retval

    # initialize
    poke_input_spline([0]*npts)
    tester.poke(dut.dt, 0)
    tester.poke(dut.clk, 0)
    tester.poke(dut.rst, 1)
    tester.eval()

    # apply reset
    tester.step(2)

    # clear reset
    tester.poke(dut.rst, 0)
    tester.step(2)

    # apply segments (chosen from a particularly bad case observed on an FPGA)
    dtlist = [0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960,
              0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080,
              0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960,
              0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960,
              0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080]
    t = 0
    tlist = []
    ylist = []
    for dt in dtlist:
        tlist.append(t)
        poke_input_spline(my_interp(t+svec*dtmax))
        tester.poke(dut.dt, dt)
        tester.eval()
        ylist.append(get_output_spline())
        tester.step(2)
        t += dt*dtmax

    # run the simulation
    tester.compile_and_run(
        directory=BUILD_DIR,
        simulator=simulator,
        ext_srcs=[model_file, get_file('ctle_interp2/test_ctle_interp2.sv')],
        real_type=real_type,
        # dump_waveforms=True
    )

    # convert measurements to arrays
    ylist = [np.array([pt.value for pt in seg]) for seg in ylist]

    # calculate measured values
    idx0 = np.where(t_resp >= tlist[0])[0][0]
    idx1 = np.where(t_resp >= tlist[-1])[0][0]
    t_interp = t_resp[idx0:(idx1+1)]
    y_meas = interp_emu_res(tlist, ylist, dtmax, t_interp, order, npts)

    # find expected response of the CTLE
    num, den = calc_ctle_num_den(fz=fz*dtmax, fp1=fp1*dtmax, gbw=gbw*dtmax)
    b, a, _ = cont2discrete((num, den), dt=tover/dtmax)
    y_expt = lfilter(b[0], a, v_resp)

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.plot(t_resp, y_expt)
    # plt.plot(t_interp, y_meas)
    # plt.plot(tlist, [elem[0] for elem in ylist], 'o')
    # plt.legend(['y_expt', 'y_meas'])
    # plt.show()

    # calculate error
    rms_err = np.sqrt(np.mean((y_expt[idx0:(idx1+1)]-y_meas)**2))
    print('rms_err:', rms_err)
    assert rms_err < err_lim
