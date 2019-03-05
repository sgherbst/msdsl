from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.expr import to_real, to_sint, to_uint, min_op, max_op

def clamp(a, min_val, max_val):
    return min_op([max_op([a, min_val]), max_val])

def main():
    model = MixedSignalModel('model')

    model.add_analog_input('a_in')
    model.add_digital_output('d_out', width=8)

    model.add_analog_output('a_out')
    model.add_digital_input('d_in', width=8)

    # DAC from 0 to 1V as the input code varies from 0-255

    clamped = clamp(to_sint(model.a_in*255, width=model.d_out.width+1), 0, 255)
    model.set_this_cycle(model.d_out, to_uint(clamped, width=model.d_out.width))

    # ADC code goes from 0-255 as input voltage goes from 0 to 1V

    model.set_this_cycle(model.a_out, model.d_in/255)

    gen = VerilogGenerator()
    model.compile_model(gen)

    print(gen.text)

if __name__ == '__main__':
    main()