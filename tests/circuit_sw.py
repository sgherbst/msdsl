from msdsl import MixedSignalModel, VerilogGenerator, AnalogSignal

def main():
    dt = 0.1e-6

    m = MixedSignalModel('model', dt=dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')
    m.add_digital_input('sw1')
    m.add_digital_input('sw2')

    c = m.make_circuit()
    gnd = c.make_ground()

    c.voltage('net_v_in', gnd, m.v_in)
    c.switch('net_v_in', 'net_v_x', m.sw1, r_on=1.0, r_off=2.0)
    c.switch('net_v_x', gnd, m.sw2, r_on=3.0, r_off=4.0)

    c.add_eqns(
        AnalogSignal('net_v_x') == m.v_out
    )

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()