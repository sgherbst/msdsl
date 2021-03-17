import numpy as np
from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
dt = m.add_analog_input('dt')
y = m.add_analog_output('y')
func = lambda dt: np.exp(-dt/(r*c))
f = m.make_function(func,
    domain=[0, 10*r*c], numel=512, order=1)
a = m.set_from_sync_func('a', f, dt)
x_prev = m.cycle_delay(x, 1)
y_prev = m.cycle_delay(y, 1)
m.set_this_cycle(y, a*y_prev + (1-a)*x_prev)
m.compile_and_print(VerilogGenerator())