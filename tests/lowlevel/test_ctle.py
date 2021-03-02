import pytest
import numpy as np
from scipy.interpolate import interp1d
from scipy.signal import lfilter
from scipy.signal import cont2discrete
from msdsl.interp.interp import calc_interp_w
from msdsl.interp.lds import SplineLDS
from msdsl.interp.ctle import calc_ctle_abcd, calc_ctle_num_den


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


@pytest.mark.parametrize('fz,fp1,npts', [
    (0.8e9, 1.6e9, 4),
    (3.5e9, 7e9, 4),
    (5e9, 10e9, 4),
    (0.8e9, 1.6e9, 5),
    (3.5e9, 7e9, 5),
    (5e9, 10e9, 5),
    (0.8e9, 1.6e9, 6),
    (3.5e9, 7e9, 6),
    (5e9, 10e9, 6)
])
def test_ctle(fz, fp1, npts, order=3, gbw=40e9, dtmax=62.5e-12, nover=100000, err_lim=1e-4):
    # normalize frequencies
    fz = fz*dtmax
    fp1 = fp1*dtmax
    gbw = gbw*dtmax

    # calculate system representation
    num, den = calc_ctle_num_den(fz=fz, fp1=fp1, gbw=gbw)
    A, B, C, D = calc_ctle_abcd(fz=fz, fp1=fp1, gbw=gbw)

    # define input segments
    seg1 = make_cubic_func(-2, 0, -0.25, 1.75)
    seg2 = make_cubic_func(1.75, 0, 0.1, -0.3)
    seg3 = make_cubic_func(-0.3, -0.1, -0.1, 1.25)

    # calculate response using conventional method
    tvec = np.linspace(0, 1, nover)
    xvec = np.concatenate((seg1(tvec[:-1]), seg2(tvec[:-1]), seg3(tvec)))
    b, a, _ = cont2discrete((num, den), dt=1/(nover-1))
    y_expt = lfilter(b[0], a, xvec)

    # calculate response using spline method
    svec = np.linspace(0, 1, npts)
    W = calc_interp_w(npts=npts, order=order)
    ctle = SplineLDS(A=A, B=B, C=C, D=D, W=W)
    x = np.zeros((A.shape[0],), dtype=float)
    x, y1_meas = ctle.calc_update(xo=x, inpt=seg1(svec), dt=1)
    x, y2_meas = ctle.calc_update(xo=x, inpt=seg2(svec), dt=1)
    x, y3_meas = ctle.calc_update(xo=x, inpt=seg3(svec), dt=1)

    # check the output a certain specific points
    y1_expt = y_expt[(0*(nover-1)):((1*nover)-0)]
    y2_expt = y_expt[(1*(nover-1)):((2*nover)-1)]
    y3_expt = y_expt[(2*(nover-1)):((3*nover)-2)]

    # sanity check to make sure slices are OK
    assert len(y1_expt) == nover
    assert len(y2_expt) == nover
    assert len(y3_expt) == nover

    # # uncomment for debugging
    # import matplotlib.pyplot as plt
    # plt.plot(tvec, y1_expt, '-')
    # plt.plot(svec, y1_meas, 'o')
    # plt.show()
    # plt.plot(tvec, y2_expt, '-')
    # plt.plot(svec, y2_meas, 'o')
    # plt.show()
    # plt.plot(tvec, y3_expt, '-')
    # plt.plot(svec, y3_meas, 'o')
    # plt.show()

    # sample output of conventional method
    y1_expt_i = interp1d(tvec, y1_expt)(svec)
    y2_expt_i = interp1d(tvec, y2_expt)(svec)
    y3_expt_i = interp1d(tvec, y3_expt)(svec)

    # run comparisons
    assert np.max(np.abs(y1_meas - y1_expt_i)) < err_lim
    assert np.max(np.abs(y2_meas - y2_expt_i)) < err_lim
    assert np.max(np.abs(y3_meas - y3_expt_i)) < err_lim
