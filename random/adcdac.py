from msdsl import *
m = MixedSignalModel('model')
vref = 1.2
# DAC
d_in = m.add_digital_input('d_in', width=8)
a_out = m.add_analog_output('a_out')
m.set_this_cycle(a_out, vref*(d_in/256))
# ADC
a_in = m.add_analog_input('a_in')
d_out = m.add_digital_output('d_out', width=9, signed=True)
m.set_this_cycle(d_out, to_sint((a_in/vref)*256, width=9))
m.compile_and_print(VerilogGenerator())
