from msdsl.circuit import Circuit

# create new circuit
cir = Circuit()

# create variables
input_ = cir.external('input')
v_in, v_out = cir.internal('v_in', 'v_out')

# instantiate linear elements
cir.voltage_source(v_in, 0, input_)
cir.resistor(v_in, v_out, 1e3)
cir.resistor(v_out, 0, 2e3)

# solve the circuit
cir.solve(v_out)
