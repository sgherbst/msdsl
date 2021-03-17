from msdsl import *
from math import exp, sqrt
r, c, dt, k, T = 1e3, 1e-9, 0.1e-6, 1.38e-23, 300
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
y = m.add_analog_output('y')
rms = sqrt(2*k*T*r/dt)
n = m.set_gaussian_noise('n', std=rms)
a = exp(-dt/(r*c))
m.set_next_cycle(y, a*y + (1-a)*(x+n))
m.compile_and_print(VerilogGenerator())