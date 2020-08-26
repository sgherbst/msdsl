# results:

# using np.random.normal
# with 100,000,000 pts: can verify 5 sigma to 5%, 3/4 sigma to 1%, 2 sigma and below to 0.1%
# with 10,000,000 pts: can verify 4 sigma to 5%, 3 sigma to 2%, 2 sigma to 0.5%, 1 sigma to 0.1%
# with 1,000,000 pts: can verify 3 sigma to 5%, 2/1 sigma to 1%
# with 100,000 pts: can verify 2 sigma to 2%, 1 sigma to 1%

# using Xcelium simulation $dist_normal(seed, 0, 10000)/10000.0
# with 1,000,000,000: can verify 5/6 sigma to 5%, 4 sigma and below to better than 1%

# With msdsl, 1/2 sigma are good to within 1%, but the error rate is already off by 36% at 3 sigma
# 4 sigma and beyond are very far off

import numpy as np
from scipy.stats import norm

N_PTS = 100000000

# using numpy.normal
# data = np.random.normal(size=N_PTS)

# using msdsl
from scipy.stats import truncnorm
from msdsl import Function
inv_cdf = lambda x: truncnorm.ppf(x, -10, +10)
func = Function(inv_cdf, domain=[0.0, 0.5], order=1, numel=512, log_bits=7)
unf_noise = np.random.uniform(-0.5, 0.5, N_PTS)
unf_noise_sgn = np.sign(unf_noise)
data = func.eval_on(np.abs(unf_noise)) * unf_noise_sgn

# construct emperical CDF
data_sorted = np.sort(data)
p = 1. * np.arange(len(data)) / (len(data) - 1)

# compare results
test_pts = np.linspace(-6, 6, 13)
meas_cdf = np.interp(test_pts, data_sorted, p)
expct_cdf = norm.cdf(test_pts)

# print results
for k in range(len(test_pts)):
    if test_pts[k] > 0:
        meas = 1 - meas_cdf[k]
        expct = 1 - expct_cdf[k]
    else:
        meas = meas_cdf[k]
        expct = expct_cdf[k]
    rel_err = (meas-expct)/expct
    print(f'{test_pts[k]}: meas {meas:e}, expct {expct:e}, rel_err {rel_err*100:0.3f}%')