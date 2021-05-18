import numpy as np
from msdsl import *
m = MixedSignalModel('rc')
dt = m.add_analog_input('dt')
alpha = m.add_analog_output('alpha')
func = lambda dt: np.exp(-dt)
f = m.make_function(func, domain=[0, 10], numel=512, order=1)
m.set_from_sync_func(alpha, f, dt)
m.compile_and_print(VerilogGenerator())