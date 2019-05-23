from msdsl.circuit import Circuit

from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator

def main():
    dt = 0.1e-6
    res = 1e3
    cap = 1e-9

    m = MixedSignalModel('model', dt=dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_analog_output('i_in')
    m.add_analog_input('i_out')

    v_cap = m.add_analog_state('v_cap', range_=10)

    c = Circuit()
    c.capacitor('net_v_out', 'gnd', cap, v_cap)
    c.resistor('net_v_in', 'net_v_out', res)
    c.current_source('net_v_out', 'gnd', m.i_out, m.v_out)
    c.voltage_source('net_v_in', 'gnd', m.v_in, m.i_in)

    eqns = c.compile()
    m.add_eqn_sys(eqns)

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()