import numpy as np
from msdsl import *
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
dt = m.add_analog_input('dt')
y = m.add_analog_output('y')
func = m.make_function(lambda t: np.exp(-t/1e-6),
    domain=[0, 1e-6], numel=512, order=1)
f = m.set_from_sync_func('f', func, dt)
x_prev = m.cycle_delay(x, 1)
y_prev = m.cycle_delay(y, 1)
m.set_this_cycle(y, f*y_prev + (1-f)*x_prev)
m.compile_and_print(VerilogGenerator())