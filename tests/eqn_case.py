from msdsl import MixedSignalModel, VerilogGenerator, Deriv, eqn_case

def main():
    tau = 1e-6
    dt = 0.1e-6

    model = MixedSignalModel('model', dt=dt)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out')
    model.add_digital_input('ctrl')

    model.add_eqn_sys([Deriv(model.v_out) == eqn_case([0, 1/tau], [model.ctrl])*model.v_in - model.v_out/tau])

    model.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()