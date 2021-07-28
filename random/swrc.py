from msdsl import *
r0, r1, c = 1234, 2345, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
u = m.add_analog_input('u')
k = m.add_digital_input('k')
x = m.add_analog_output('x')
g = eqn_case([1/r0, 1/r1], [k])
m.add_eqn_sys([c*Deriv(x) == (u-x)*g])
m.compile_and_print(VerilogGenerator())