from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.eqn.deriv import Deriv
from msdsl.expr.signals import AnalogSignal

def main():
    dt = 0.01e-6
    cap = 0.16e-6
    ind = 0.16e-6
    res = 0.1

    model = MixedSignalModel('model', dt=dt)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out')

    model.add_analog_state('i_ind', 100)

    v_l = AnalogSignal('v_l')
    v_r = AnalogSignal('v_r')
    eqns = [
        Deriv(model.i_ind) == v_l/ind,
        Deriv(model.v_out) == model.i_ind/cap,
        v_r == model.i_ind*res,
        model.v_in == model.v_out + v_l + v_r
    ]
    model.add_eqn_sys(eqns)

    gen = VerilogGenerator()
    model.compile_model(gen)

    print(gen.text)

if __name__ == '__main__':
    main()