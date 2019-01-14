from msdsl.generator import CodeGenerator
from msdsl.util import adder_tree

class AnalogModel:
    def __init__(self, name='analog_model', inputs=None, outputs=None, dt=None):
        # set defaults
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        # save settings
        self.name = name
        self.inputs = inputs
        self.outputs = outputs
        self.dt = dt

        # create signal objects
        self.signals = {}

    def run_generator(self, gen: CodeGenerator):
        # start module
        gen.start_module(name=self.name, inputs=self.inputs, outputs=self.outputs)

        # main model
        for output in self.outputs:
            # label this section of the code for debugging purposes
            gen.section(f'Updating signal: {output}')

            # compute products of coefficients with signals
            prod_vars = [gen.mul_const_real(coeff, var) for var, coeff in self.signals[output].items()]

            # add up all of these products
            sum_var = adder_tree(prod_vars,
                                 zero_func=lambda: gen.make_const_real(0),
                                 add_func=lambda a, b: gen.add_real(a, b))

            # update value of output
            gen.mem_into_real(sum_var, output)

        # end module
        gen.end_module()
