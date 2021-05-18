from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
circ = m.make_circuit()
gnd = circ.make_ground()
circ.capacitor('net_y', gnd, c, voltage_range=RangeOf(x))
circ.resistor('net_x', 'net_y', r)
circ.voltage('net_x', gnd, x)
circ.add_eqns(AnalogSignal('net_y') == y)
m.compile_and_print(VerilogGenerator())
