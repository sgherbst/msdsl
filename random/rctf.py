from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
m.set_tf(x, y, [[1], [r*c, 1]])
m.compile_and_print(VerilogGenerator())