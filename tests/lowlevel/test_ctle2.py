import pytest
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d
from scipy.signal import lfilter
from scipy.signal import cont2discrete
from msdsl.interp.interp import calc_interp_w
from msdsl.interp.lds import SplineLDS
from msdsl.interp.ctle import calc_ctle_abcd, calc_ctle_num_den
from msdsl.interp.interp import calc_piecewise_poly, eval_piecewise_poly

THIS_DIR = Path(__file__).resolve().parent
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

@pytest.mark.parametrize('fz,fp1,npts,order,gbw,dtmax,err_lim', [
    (0.8e9, 1.6e9, 4, 3, 40e9, 31.25e-12, 5e-3),
])
def test_ctle2(fz, fp1, npts, order, gbw, dtmax, err_lim):
    # normalize frequencies
    fz = fz*dtmax
    fp1 = fp1*dtmax
    gbw = gbw*dtmax

    # read in data
    my_data = np.genfromtxt(DATA_FILE, delimiter=',', skip_header=1)
    t_resp = my_data[:, 1] - my_data[0, 1]
    v_resp = my_data[:, 2]

    # find timestep of oversampled data
    tover = np.median(np.diff(t_resp))
    assert np.all(np.isclose(np.diff(t_resp), tover))
    print(f'tover: {tover*1e12:0.3f} ps')

    # build interpolator for data
    my_interp = interp1d(t_resp, v_resp)
    svec = np.linspace(0, 1, npts)

    # find state-space representation of the CTLE
    A, B, C, D = calc_ctle_abcd(fz=fz, fp1=fp1, gbw=gbw)

    # calculate response using spline method
    # the list of timesteps used is one that was found to be particularly bad for the emulator
    W = calc_interp_w(npts=npts, order=order)
    ctle = SplineLDS(A=A, B=B, C=C, D=D, W=W)
    x = np.zeros((A.shape[0],), dtype=float)
    t = 0
    dtlist = [0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960,
              0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080,
              0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960,
              0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080, 0.960, 0.960,
              0.080, 0.960, 0.960, 0.080, 0.960, 0.960, 0.080]
    tlist = []
    ylist = []
    for dt in dtlist:
        tlist.append(t)
        x, y = ctle.calc_update(xo=x, inpt=my_interp(t+svec*dtmax), dt=dt)
        ylist.append(y)
        t += dt*dtmax

    # calculate measured values
    y_meas = interp_emu_res(tlist, ylist, dtmax, t_resp, order, npts)

    # find expected response of the CTLE
    num, den = calc_ctle_num_den(fz=fz, fp1=fp1, gbw=gbw)
    b, a, _ = cont2discrete((num, den), dt=tover/dtmax)
    y_expt = lfilter(b[0], a, v_resp)

    # uncomment to plot results
    # import matplotlib.pyplot as plt
    # plt.plot(t_resp, y_expt)
    # plt.plot(t_resp, y_meas)
    # plt.show()

    # calculate error
    rms_err = np.sqrt(np.mean((y_expt-y_meas)**2))
    print('rms_err:', rms_err)
    assert rms_err < err_lim
