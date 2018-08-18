from msdsl.circuit import Circuit
from msdsl.format import dump_model

# create new circuit
cir = Circuit()

# create variables
input_ = cir.input_('input')
v_in, v_out = cir.nodes('v_in', 'v_out')

# instantiate linear elements
cir.voltage_source(v_in, 0, input_)
cir.resistor(v_in, v_out, 1e3)
cir.capacitor(v_out, 0, 1e-9)

# solve the circuit
dump_model(cir.solve(10e-9, [v_out]))
