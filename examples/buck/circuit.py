import sys
import logging

from msdsl.circuit import Circuit
from msdsl.format import dump_model

logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

# ref: http://www.simonbramble.co.uk/dc_dc_converter_design/buck_converter/buck_converter_design.htm

# create new circuit
cir = Circuit()

# Create nodes
v_in, v_sw, v_snub, v_out = cir.nodes('v_in', 'v_sw', 'v_snub', 'v_out')

# Input voltage
input_ = cir.input_('input')
cir.voltage_source(v_in, 0, expr=input_)

# MOSFET
cir.mosfet(v_in, v_sw)

# Diode
diode = cir.diode(0, v_sw)

# Snubber
cir.capacitor(v_sw, v_snub, value=1e-12)
cir.resistor(v_snub, 0, value=3.9e3)

# Filter
ind = cir.inductor(v_sw, v_out, value=4.7e-6)
cir.capacitor(v_out, 0, value=150e-6)

# Output load
cir.resistor(v_out, 0, value=20)

# Define outputs
cir.output(v_out)
cir.output(ind.port.i, 'i_mag')

# Solve the circuit
cir.solve(2e-9)

# Dump the model
dump_model(cir.model)