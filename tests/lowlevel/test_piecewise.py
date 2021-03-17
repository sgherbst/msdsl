import numpy as np
from msdsl.interp.interp import (myinterp, eval_piecewise_poly, eval_poly, ovl_pwp_mats,
                                 calc_interp_w, calc_piecewise_poly)

def test_myinterp():
    x0, a0 = 0.234, 1.23
    x1, a1 = 0.345, 2.34
    x2, a2 = 0.456, 3.45

    f = myinterp([x0, x1, x2], [a0, a1, a2])

    assert np.isclose(f(-1), a0)
    assert np.isclose(f(x0), a0)
    assert np.isclose(f(0.5*(x0+x1)), 0.5*(a0+a1))
    assert np.isclose(f(x1), a1)
    assert np.isclose(f(0.5*(x1+x2)), 0.5*(a1+a2))
    assert np.isclose(f(x2), a2)
    assert np.isclose(f(+1), a2)

def test_eval_pwp():
    a0 = 1.23
    a1 = 2.34
    a2 = 3.45

    U = np.zeros((3, 2), dtype=float)
    U[0, :] = [a0, a1-a0]
    U[1, :] = [a1, a2-a1]
    U[2, :] = [a2, 0]

    f = lambda t: eval_piecewise_poly(t, 1, U)

    assert np.isclose(f(0), a0)
    assert np.isclose(f(0.5), 0.5*(a0+a1))
    assert np.isclose(f(1), a1)
    assert np.isclose(f(1.5), 0.5*(a1+a2))
    assert np.isclose(f(2), a2)

    assert np.all(np.isclose(f([0, 0.5, 1, 1.5, 2]), [a0, 0.5*(a0+a1), a1, 0.5*(a1+a2), a2]))

def test_eval_poly():
    x = 0.876
    assert np.all(np.isclose(eval_poly(x, 3), [x**0, x**1, x**2, x**3]))

def test_ovl_mats():
    # this test case is a little complicated, because it needs to
    # hit the two edge cases in ovl_pwp_mats, as well as the normal case

    A, B = ovl_pwp_mats(4, 3)

    A_expct = np.zeros((12, 12), dtype=float)
    B_expct = np.zeros((12, 4), dtype=float)

    A_expct[0, 0:4], B_expct[0, :] = [1, 0, 0, 0], [1, 0, 0, 0]
    A_expct[1, 0:4], B_expct[1, :] = [1, 1, 1, 1], [0, 1, 0, 0]
    A_expct[2, 0:4], B_expct[2, :] = [1, 2, 4, 8], [0, 0, 1, 0]
    A_expct[3, 0:4], B_expct[3, :] = [1, 3, 9, 27], [0, 0, 0, 1]

    A_expct[4, 4:8], B_expct[4, :] = [1, -1, 1, -1], [1, 0, 0, 0]
    A_expct[5, 4:8], B_expct[5, :] = [1, 0, 0, 0], [0, 1, 0, 0]
    A_expct[6, 4:8], B_expct[6, :] = [1, 1, 1, 1], [0, 0, 1, 0]
    A_expct[7, 4:8], B_expct[7, :] = [1, 2, 4, 8], [0, 0, 0, 1]

    A_expct[8, 8:12], B_expct[8, :] = [1, -2, 4, -8], [1, 0, 0, 0]
    A_expct[9, 8:12], B_expct[9, :] = [1, -1, 1, -1], [0, 1, 0, 0]
    A_expct[10, 8:12], B_expct[10, :] = [1, 0, 0, 0], [0, 0, 1, 0]
    A_expct[11, 8:12], B_expct[11, :] = [1, 1, 1, 1], [0, 0, 0, 1]

    assert np.all(np.isclose(A, A_expct))
    assert np.all(np.isclose(B, B_expct))

def test_w_calc():
    # w[j, k, i] maps the i-th spline point to the k-th coefficient of the j-th polynomial segment

    W = calc_interp_w(3, order=1)

    W_expct = np.zeros((3, 2, 3), dtype=float)

    W_expct[0, 0, 0] = 1
    W_expct[0, 1, 0] = -1
    W_expct[0, 1, 1] = 1

    W_expct[1, 0, 1] = 1
    W_expct[1, 1, 1] = -1
    W_expct[1, 1, 2] = 1

    W_expct[2, 0, 2] = 1

    assert np.all(np.isclose(W, W_expct))


def test_calc_pwp():
    u0 = 1.23
    u1 = 3.77
    u2 = 7.45

    U = calc_piecewise_poly([u0, u1, u2], order=1)

    U_expct = np.zeros((3, 2), dtype=float)

    U_expct[0, 0] = u0
    U_expct[0, 1] = u1-u0

    U_expct[1, 0] = u1
    U_expct[1, 1] = u2-u1

    U_expct[2, 0] = u2

    assert np.all(np.isclose(U, U_expct))


def test_fitting():
    # more complex fitting example
    func = lambda x: (x-1.23)*(x-2.34)*(x-3.45)

    # test parameters
    xmax = 4
    npts = 6
    order = 3

    # sample spline points
    xsub = np.linspace(0, xmax, npts)
    ysub = func(xsub)

    # calculate piecewise polynomial
    U = calc_piecewise_poly(ysub, order=order)

    # evaluate PWP on a larger test set
    xtest = np.linspace(0, xmax, 1000)
    ymeas = eval_piecewise_poly(xtest, xmax/(npts-1), U)
    yexpt = func(xtest)

    # compare the two
    assert np.all(np.isclose(ymeas, yexpt))
