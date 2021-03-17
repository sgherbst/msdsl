from msdsl import *
r, rsw, c = 1e3, 100, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
s = m.add_digital_input('s')
y = m.add_analog_output('y')
g = eqn_case([1/r, 1/r+1/rsw], [s])
m.add_eqn_sys([c*Deriv(y) == (x-y)*g])
m.compile_and_print(VerilogGenerator())
