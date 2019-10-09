from msdsl import MixedSignalModel, VerilogGenerator, AnalogSignal

def main():
    dt = 1e-9

    m = MixedSignalModel('model', dt=dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('sw1')
    m.add_digital_input('sw2')

    c = m.make_circuit()
    gnd = c.make_ground()

    c.voltage('net_v_in', gnd, m.v_in)
    c.switch('net_v_in', 'net_v_x', m.sw1)
    c.switch('net_v_x', gnd, m.sw2)

    c.inductor('net_v_in', 'net_v_x', 1, current_range=100)

    c.add_eqns(
        AnalogSignal('net_v_x') == m.v_out
    )

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()
