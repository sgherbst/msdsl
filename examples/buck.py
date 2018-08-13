from msdsl.circuit import Circuit
from msdsl.util import to_json

# create new circuit
cir = Circuit()

# create nodes
v_in, v_sw, v_out = cir.internal('v_in', 'v_sw', 'v_out')

# input voltage
input_ = cir.external('input')
cir.voltage_source(v_in, 0, expr=input_)

# switches
cir.mosfet(v_in, v_sw)
diode = cir.diode(0, v_sw)

# filter
ind = cir.inductor(v_sw, v_out, value=10e-6)
cir.capacitor(v_out, 0, value=10e-6)

# output load
output = cir.external('output')
cir.current_source(v_out, 0, expr=output)

# solve the circuit
print(to_json(cir.solve(0.25e-6, [v_out])))