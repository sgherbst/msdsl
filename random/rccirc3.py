from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
vin = m.add_analog_input('vin')
iin = m.add_analog_output('iin')  # note: output
vout = m.add_analog_output('vout')
iout = m.add_analog_input('iout')  # note: input
circ = m.make_circuit()
gnd = circ.make_ground()
circ.capacitor('net_vout', gnd, c, voltage_range=RangeOf(vin))
circ.resistor('net_vin', 'net_vout', r)
c_iin = circ.voltage('net_vin', gnd, vin)
circ.current('net_vout', gnd, iout)
circ.add_eqns(
    iin == -c_iin,
    vout == AnalogSignal('net_vout')
)
m.compile_and_print(VerilogGenerator())
