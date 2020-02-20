from msdsl import MixedSignalModel, VerilogGenerator, RangeOf, AnalogSignal

def main():
    dt = 0.1e-6
    res = 1e3
    cap = 1e-9

    m = MixedSignalModel('model', dt=dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    c = m.make_circuit()
    gnd = c.make_ground()

    c.capacitor('net_v_out', gnd, cap, voltage_range=RangeOf(m.v_out))
    c.resistor('net_v_in', 'net_v_out', res)
    c.voltage('net_v_in', gnd, m.v_in)

    c.add_eqns(
        AnalogSignal('net_v_out') == m.v_out
    )

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()