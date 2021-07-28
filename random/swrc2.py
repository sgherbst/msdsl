from msdsl import *
r00, r01, r10, r11, c = 123, 234, 345, 456, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
u = m.add_analog_input('u')
s0 = m.add_digital_input('s0')
s1 = m.add_digital_input('s1')
x = m.add_analog_output('x')
g0 = eqn_case([1/r00, 1/r01], [s0])
g1 = eqn_case([1/r10, 1/r11], [s1])
v = AnalogSignal('v')
m.add_eqn_sys([
    (u - v) * g0 == (v - x) * g1,
    (v - x) * g1 == c * Deriv(x)
])
m.compile_and_print(VerilogGenerator())