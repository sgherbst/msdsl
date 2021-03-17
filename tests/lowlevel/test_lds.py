import pytest
import numpy as np
from numpy import heaviside
from scipy.integrate import quad
from scipy.linalg import expm
from msdsl.interp.lds import calc_expm_integral, calc_lds_f, calc_lds_g


A = np.array([[-8.7, -6.5], [4.3, 2.1]], dtype=float)
B = np.array([[2.3], [3.4]], dtype=float)
C = np.array([[4.5, 5.6]], dtype=float)
D = np.array([[7.8]], dtype=float)


npts = 6
order = 3
th = 1/(npts-1)


@pytest.mark.parametrize('k', list(range(order+1)))
def test_expm_int(k):
    lb = 1*th
    ub = 4*th

    meas = calc_expm_integral(A, k, lb, ub)

    expt = np.zeros_like(A)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            func = lambda tau: (expm(tau*A)[i, j])*(tau**k)
            expt[i, j] = quad(func, lb, ub)[0]

    assert np.all(np.isclose(meas, expt))


@pytest.mark.parametrize('p', list(range(npts)))
@pytest.mark.parametrize('j', list(range(npts-1)))
@pytest.mark.parametrize('k', list(range(order+1)))
def test_f_calc(p, j, k):
    meas = calc_lds_f(A, B, C, th, p, j, k)

    func = lambda tau: C.dot(expm((p*th-tau)*A).dot(B))*(((tau-j*th)/th)**k)
    expt = quad(func, j*th, (j+1)*th)[0]

    assert np.all(np.isclose(meas, expt))


@pytest.mark.parametrize('j', list(range(npts-1)))
@pytest.mark.parametrize('k', list(range(order+1)))
@pytest.mark.parametrize('t', [0.123, 0.456, 0.789])
def test_g_calc(j, k, t):
    meas = calc_lds_g(A, B, th, j, k, t)

    expt = np.zeros_like(B)
    H_tilde = lambda tau: heaviside(tau-j*th, 0.5) - heaviside(tau-(j+1)*th, 0.5)
    for idx in range(B.shape[0]):
        func = lambda tau: expm((t-tau)*A).dot(B)[idx, 0]*(((tau-j*th)/th)**k)*H_tilde(tau)
        expt[idx, 0] = quad(func, 0, t)[0]

    assert np.all(np.isclose(meas, expt))
