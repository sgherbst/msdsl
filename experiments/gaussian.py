import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from msdsl import Function
from scipy.stats import truncnorm

inv_cdf = lambda x: truncnorm.ppf(x, -8, 8)
num_bits = 31  # 31 because the top bit is used to determine the sign

num_test = 10000
test_pts = 2**(np.random.uniform(0, num_bits, num_test))
test_pts = np.floor(test_pts).astype(np.int)
test_pts = np.append(test_pts, 0)
test_pts = np.sort(test_pts)

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

# calculate domain
domain = [map_f(0), map_f((1<<num_bits)-1)]
print(f'domain={domain}')

func = Function(lambda x: inv_cdf(unmap_f(x)/(1<<(num_bits+1))),
                domain=domain, order=1, numel=512)
meas = func.eval_on(map_f(test_pts))
expct = inv_cdf(test_pts/(1<<(num_bits+1)))
err = meas - expct

idx = np.argmax(np.abs(err))
print(f'Worst error: {err[idx]} @ {test_pts[idx]}')

plt.semilogx(test_pts[1:], meas[1:])
plt.semilogx(test_pts[1:], expct[1:])
plt.legend(['meas', 'expct'])
plt.show()
