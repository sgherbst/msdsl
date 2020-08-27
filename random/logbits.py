import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# using msdsl
from scipy.stats import truncnorm
from msdsl import Function
inv_cdf = lambda x: truncnorm.ppf(x, -6, +6)
func = Function(inv_cdf, domain=[0.0, 0.5], order=1, numel=512, log_bits=5)
# print(func.get_samp_points_spline())
# for elem in func.get_samp_points_spline():
#     print(elem)
#     print(func.calc_addr(elem))

# compare results
test_pts = np.linspace(0, 0.5, 1000)

plt.plot(test_pts, inv_cdf(test_pts))
plt.plot(test_pts, func.eval_on(test_pts))
plt.show()