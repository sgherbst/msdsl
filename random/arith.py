from msdsl import *
m = MixedSignalModel('model')
a = m.add_analog_input('a')
b = m.add_analog_input('b')
c = m.add_analog_output('c')
m.set_this_cycle(c, a-b)
m.compile_and_print(VerilogGenerator())