from msdsl.circuit import Circuit
from msdsl.util import to_json

# create new circuit
cir = Circuit()

# create nodes
v_in, v_sw, v_out = cir.internal('v_in', 'v_sw', 'v_out')

# input voltage
input_ = cir.external('input')
cir.voltage_source(v_in, 0, expr=input_)

# inductor
cir.inductor(v_in, v_sw, value=10e-6)

# switches
cir.mosfet(v_sw, 0)
diode = cir.diode(v_sw, v_out)

# filter
cir.capacitor(v_out, 0, value=10e-6)

# output load
output = cir.external('output')
cir.current_source(v_out, 0, expr=output)

# solve the circuit
print(to_json(cir.solve(0.25e-6, [v_out])))