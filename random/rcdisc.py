from msdsl import *
from math import exp
r, c, dt = 1e3, 1e-9, 0.1e-6
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
y = m.add_analog_output('y')
a = exp(-dt/(r*c))
m.set_next_cycle(y, a*y + (1-a)*x)
m.compile_and_print(VerilogGenerator())