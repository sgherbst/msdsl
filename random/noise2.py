from msdsl import *
from scipy.stats import truncnorm
m = MixedSignalModel('model')
y = m.add_analog_output('y')
inv_cdf = lambda x: truncnorm.ppf(x, -8, +8)
inv_cdf_func = m.make_function(inv_cdf, domain=[0.0, 1.0])
m.set_this_cycle(y, m.arbitrary_noise(inv_cdf_func))
m.compile_and_print(VerilogGenerator())