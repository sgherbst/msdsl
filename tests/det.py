from msdsl import MixedSignalModel, VerilogGenerator, Deriv, eqn_case

def main():
    tau_det_fast = 1e-9
    tau_det_slow = 360e-9
    dt = 4.6e-9

    m = MixedSignalModel('model', dt=dt)
    m.add_analog_input('v_in')
    m.add_analog_output('v_out')

    m.bind_name('in_gt_out', m.v_in > m.v_out)

    # detector dynamics
    m.add_eqn_sys([
        Deriv(m.v_out) == eqn_case([0, 1 / tau_det_fast], [m.in_gt_out]) * (m.v_in - m.v_out) - (m.v_out / tau_det_slow)
    ])

    m.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()