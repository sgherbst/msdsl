from msdsl import *
# declare I/O
m = MixedSignalModel('buck', dt=0.1e-6)
sw = m.add_digital_input('sw')
v_in = m.add_analog_input('v_in')
v_out = m.add_analog_output('v_out')
# create circuit
c = m.make_circuit()
gnd = c.make_ground()
# input
c.voltage('net_v_in', gnd, v_in)
# transistor + diode
c.switch('net_v_in', 'net_v_sw', sw, r_on=1.0, r_off=10e3)
c.diode(gnd, 'net_v_sw', r_on=1.0, r_off=10e3)
# snubber
c.capacitor('net_v_sw', 'net_v_x', 100e-12, voltage_range=100.0)
c.resistor('net_v_x', gnd, 300)
# inductor + capacitor
c.inductor('net_v_sw', 'net_v_out', 2.2e-6, current_range=20.0)
c.capacitor('net_v_out', gnd, 10e-6, voltage_range=10.0)
# load
c.resistor('net_v_out', gnd, 5.5)
# assign outputs
c.add_eqns(v_out == AnalogSignal('net_v_out'))
# print output
m.compile_and_print(VerilogGenerator())