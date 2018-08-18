from msdsl.circuit import Circuit
from msdsl.format import dump_model

# create new circuit
cir = Circuit()

# create nodes
v_in, v_sw_1, v_sw_2, v_out = cir.nodes('v_in', 'v_sw_1', 'v_sw_2', 'v_out')

# input voltage
input_ = cir.input_('input')
cir.voltage_source(v_in, 0, expr=input_)

# magnetizing inductor
ind = cir.inductor(v_in, v_sw_1, value=10e-6)

# primary switch
cir.mosfet(v_sw_1, 0)

# transformer
cir.transformer(v_in, v_sw_1, 0, v_sw_2, n=1)

# diode
diode = cir.diode(v_sw_2, v_out)

# filter
cir.capacitor(v_out, 0, value=10e-6)

# output load
output = cir.input_('output')
cir.current_source(v_out, 0, expr=output)

# solve the circuit
dump_model(cir.solve(0.25e-6, [v_out]))