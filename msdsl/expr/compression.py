import numpy as np
import numpy.ma as ma

def apply_compression(r):
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

def invert_compression(r):
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
