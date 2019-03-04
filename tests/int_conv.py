from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator
from msdsl.expr.expr import to_real, to_sint, to_uint, min_op, max_op

def clamp(a, min_val, max_val):
    return min_op([max_op([a, min_val]), max_val])

def main():
    model = MixedSignalModel('model')
    model.add_analog_input('a')
    model.add_digital_input('b', width=8)
    model.add_digital_output('c', width=12)

    print(model.a+model.b)
    model.bind_name('d', model.a+model.b)

    clamped = clamp(to_sint(model.d, width=model.c.width+1), 0, 1023)
    model.set_next_cycle(model.c, to_uint(clamped, width=model.c.width))

    gen = VerilogGenerator()
    model.compile_model(gen)

    print(gen.text)

if __name__ == '__main__':
    main()