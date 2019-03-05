from msdsl.model import MixedSignalModel
from msdsl.generator.verilog import VerilogGenerator

def main():
    model = MixedSignalModel('model')
    model.add_analog_input('a')
    model.add_analog_input('b')

    model.bind_name('c', model.a+model.b)

    gen = VerilogGenerator()
    model.compile_model(gen)

    print(gen.text)

if __name__ == '__main__':
    main()