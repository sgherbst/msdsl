from msdsl import MixedSignalModel, VerilogGenerator

def main():
    dt = 0.1e-6

    m = MixedSignalModel('model', dt=dt)

    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    m.add_eqn_sys([
        m.v_out == 0.123*m.v_in
    ])

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()