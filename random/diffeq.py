from msdsl import *
r, c, dt = 1e3, 1e-9, 0.1e-6
m = MixedSignalModel('rc', dt=dt)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
m.add_eqn_sys([c*Deriv(y) == (x-y)/r])
m.compile_and_print(VerilogGenerator())
