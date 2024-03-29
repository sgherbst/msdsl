from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
m.add_eqn_sys([c*Deriv(y) == (x-y)/r])
m.compile_and_print(VerilogGenerator())
