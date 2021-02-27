import numpy as np
from scipy.interpolate import interp1d


# convenience function: return interpolator that extends boundary values
def myinterp(x, y):
    return interp1d(x, y, bounds_error=False, fill_value=(y[0], y[-1]))


# calculate coefficients of a polynomial that fits x, y points
# the polynomial order is len(x)-1 (e.g., 3 points yields quadratic)
def calc_piecewise_poly(u, order=3, strategy='overlap'):
    # solve the linear system of equations
    W = calc_interp_w(npts=len(u), order=order, strategy=strategy)

    # generate coefficients
    U = (W*u).sum(axis=2)

    # return coefficients
    return U


# calculate the tensor, "W", that maps input points
# to coefficients of polynomial segments.  w[j, k, i] maps
# the i-th spline point to the k-th coefficient of the
# j-th polynomial segment.
def calc_interp_w(npts, order=3, strategy='overlap'):
    # set up equations
    if strategy == 'overlap':
        A, B = ovl_pwp_mats(npts=npts, order=order)
    else:
        raise Exception(f'Unknown strategy: {strategy}')

    # solve the equations
    C = np.linalg.solve(A, B)

    # fill in the W tensor
    W = np.zeros((npts, order+1, npts), dtype=float)
    W[:-1, :, :] = C.reshape((npts-1, order+1, npts))

    # a final PWC segment is included for make the math easier
    W[-1, 0, -1] = 1

    # return W tensor
    return W


# return matrices for piecewise-polynomial fit
def ovl_pwp_mats(npts, order):
    # create empty equation matrices
    A = np.zeros(((npts-1)*(order+1), (npts-1)*(order+1)), dtype=float)
    B = np.zeros(((npts-1)*(order+1), npts), dtype=float)

    # for the middle of the curve, how many points should
    # match below the starting point (tgt_lo) and above (tgt_hi)
    tgt_lo = order//2
    tgt_hi = order-tgt_lo

    # build up the equations
    idx = 0
    for i in range(npts-1):
        # figure out the starting and stopping matching points
        if (i-tgt_lo) < 0:
            lo = 0
            hi = lo + order
        elif (i+tgt_hi) > (npts-1):
            hi = npts-1
            lo = hi-order
        else:
            lo = i-tgt_lo
            hi = i+tgt_hi

        # add equations for each point
        offset = i*(order+1)
        for j in range(lo, hi+1):
            A[idx, offset:(offset+order+1)] = eval_poly(j-i, order=order)
            B[idx, j] = 1
            idx += 1

    return A, B


# evaluate a polynomial; return a such that
# a[k] = x^k
# sum(ak*x^k, 0, order) == sum(bk*x^k, 0, order)
def eval_poly(x, order):
    return x**np.arange(order+1)

# evaluate a piecewise polynomial waveform
# U[i, j] is the ith segment, jth coefficient (i.e., jth power)
def eval_piecewise_poly(t, th, U):
    # convert t to a numpy array if needed
    t = np.array(t)

    # calculate coefficient indices and remainders
    ivec = np.floor(t/th).astype(int)
    rvec = (t-(ivec*th))/th

    # sum contributions from each polynomial order
    pows = rvec[..., np.newaxis]**np.arange(U.shape[1])
    retval = (U[ivec, :]*pows).sum(axis=len(pows.shape)-1)

    # return result
    return retval
