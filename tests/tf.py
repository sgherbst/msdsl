from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.eqn.deriv import Deriv

def main():
    dt = 0.1e-6

    num = (1e12,)
    den = (1, 8e5, 1e12,)

    model = MixedSignalModel('model', dt=dt)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out')

    model.set_tf(input_=model.v_in, output=model.v_out, tf=(num, den))

    gen = VerilogGenerator()
    model.compile_model(gen)

    print(gen.text)

if __name__ == '__main__':
    main()