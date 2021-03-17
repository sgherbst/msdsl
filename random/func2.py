import numpy as np
from msdsl import *
m = MixedSignalModel('model')
x = m.add_analog_input('x')
y1 = m.add_analog_output('y1')
y2 = m.add_analog_output('y2')
func1 = lambda t: np.sin(t)
func2 = lambda t: np.cos(t)
f = m.make_function([func1, func2],
    domain=[-np.pi, np.pi], numel=512, order=1)
m.set_from_sync_func([y1, y2], f, x)
m.compile_and_print(VerilogGenerator())