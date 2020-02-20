from msdsl import MixedSignalModel, VerilogGenerator

def main():
    dt = 0.1e-6

    num = (1e12,)
    den = (1, 8e5, 1e12,)

    model = MixedSignalModel('model', dt=dt)
    model.add_analog_input('v_in')
    model.add_analog_output('v_out')

    model.set_tf(input_=model.v_in, output=model.v_out, tf=(num, den))

    model.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()