import numpy as np
from msdsl import Function
from scipy.stats import truncnorm

num_sigma = 6
inv_cdf = lambda x: truncnorm.ppf(x, -num_sigma, +num_sigma)

num_test = 10000
test_pts = 2**(np.random.uniform(-32, -1, num_test))

f = Function(inv_cdf, domain=[0, 0.5], numel=1024, order=1)
meas = f.eval_on(test_pts)
expct = inv_cdf(test_pts)
err = meas - expct

idx = np.argmax(np.abs(err))
print(f'Worst error: {err[idx]} @ {test_pts[idx]}')