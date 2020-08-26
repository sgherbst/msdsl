import numpy as np
import matplotlib.pyplot as plt
from msdsl import Function
from scipy.stats import norm

inv_cdf = norm.ppf
num_bits = 31  # 31 because the top bit is used to determine the sign

num_test = 10000
test_pts = 2**(np.random.uniform(0, num_bits, num_test))
test_pts = np.floor(test_pts).astype(np.int)
test_pts = np.sort(test_pts)

# logarithmic mapping
def map_f(r):
    x = np.floor(np.log2(r))
    y = (r/(2.0**x)) - 1
    return x + y
def unmap_f(r):
    x = np.floor(r)
    return (2.0**(x-num_bits-1)) * (1 + r - x)

# calculate domain
min_val = map_f(1)
max_val = map_f((1<<num_bits)-1)
domain = [min_val, max_val]
print(f'domain={domain}')

func = Function(lambda x: inv_cdf(unmap_f(x)), domain=domain, order=1, numel=512)
meas = func.eval_on(map_f(test_pts))
expct = inv_cdf(test_pts/(1<<(num_bits+1)))
err = meas - expct

idx = np.argmax(np.abs(err))
print(f'Worst error: {err[idx]} @ {test_pts[idx]}')

plt.semilogx(test_pts, meas)
plt.semilogx(test_pts, expct)
plt.legend(['meas', 'expct'])
plt.show()
