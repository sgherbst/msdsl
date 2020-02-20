from msdsl import MixedSignalModel, VerilogGenerator

def main():
    model = MixedSignalModel('model')
    model.add_analog_input('a')
    model.add_analog_input('b')

    model.bind_name('c', model.a+model.b)

    model.compile_and_print(VerilogGenerator())

if __name__ == '__main__':
    main()