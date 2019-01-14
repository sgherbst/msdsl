from msdsl.verilog import VerilogGenerator
from msdsl.util import chunks

def adder_tree(terms, gen):
    if len(terms) == 0:
        raise Exception('Summation of zero terms not handled yet.')
    elif len(terms) == 1:
        return terms[0]
    elif len(terms) == 2:
        sum_var = gen.tmpvar()
        gen.println(f'`ADD_REAL({terms[0]}, {terms[1]}, {sum_var});')
        return sum_var
    else:
        sum_vars = [adder_tree(chunk, gen) for chunk in chunks(terms, 2)]
        sum_var = adder_tree(sum_vars, gen)
        return sum_var

class AnalogModel:
    def __init__(self, name='analog_model', inputs=None, outputs=None):
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        # save settings
        self.name = name
        self.inputs = inputs
        self.outputs = outputs

        # create signal objects
        self.signals = {}

    def implement_output(self, output, dt, gen):
        # multiplications
        prod_vars = []
        for var, coeff in self.signals[output].items():
            prod_var = gen.tmpvar()
            gen.println(f'`MUL_CONST_REAL({coeff}, {var}, {prod_var});')
            prod_vars.append(prod_var)

        # additions
        sum_var = adder_tree(prod_vars, gen)

        # memory update
        gen.println(f'`MEM_INTO_REAL({sum_var}, {output});')

    def generate(self, dt, filename):
        gen = VerilogGenerator(filename)

        # set timescale
        gen.timescale()
        gen.println()

        # include real number library
        gen.include('real.sv')
        gen.println()

        # determine parameters
        parameters = [f'`DECL_REAL({io})' for io in self.inputs+self.outputs]

        # determine IOs
        ios = ['input wire logic clk', 'input wire logic rst']
        ios.extend([f'`INPUT_REAL({input})' for input in self.inputs])
        ios.extend([f'`OUTPUT_REAL({output})' for output in self.outputs])

        # start module
        gen.start_module(name=self.name, parameters=parameters, ios=ios)

        # main model
        for output in self.outputs:
            gen.comment(f'Updating signal: {output}')
            self.implement_output(output=output, dt=dt, gen=gen)
            gen.println()

        # end module
        gen.end_module()