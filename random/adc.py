from msdsl import *
m = MixedSignalModel('adc')
vref, rms = 1.2, 10e-3
a_in = m.add_analog_input('a_in')
d_out = m.add_digital_output('d_out', width=8, signed=True)
noise = m.set_gaussian_noise('noise')
out_expr = to_sint(-128+255*((a_in+rms*noise)/vref), width=8)
m.set_this_cycle(d_out, out_expr)
m.compile_and_print(VerilogGenerator())
