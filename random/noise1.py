from msdsl import *
m = MixedSignalModel('model')
y = m.add_analog_output('y')
m.set_this_cycle(y, m.uniform_signal())
m.compile_and_print(VerilogGenerator())