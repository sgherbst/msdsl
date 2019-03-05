from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.eqn.deriv import Deriv

def main():
    tau = 1e-6
    dt = 0.1e-6

    model = MixedSignalModel('model', dt=dt)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out', init=1.23)

    model.add_eqn_sys([Deriv(model.v_out) == (model.v_in - model.v_out)/tau])

    model.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()