from msdsl.generator import CodeGenerator
from msdsl.util import adder_tree
from msdsl.expr import LinearExpr

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
        self.signals = {name: LinearExpr({name: 1.0}) for name in inputs+outputs}

        # derivatives
        self.derivs = {}

    def __getattr__(self, item):
        return self.signals[item]

    def run_generator(self, gen: CodeGenerator):
        # start module
        gen.start_module(name=self.name, inputs=self.inputs, outputs=self.outputs)

        # main model
        for signal_name, deriv_expr in self.derivs.items():
            # label this section of the code for debugging purposes
            gen.section(f'Updating signal: {signal_name}')

            # compute forward euler
            update_expr = self.dt*deriv_expr + self.signals[signal_name]

            # compute products of coefficients with signals
            prod_vars = [gen.mul_const_real(coeff, var) for var, coeff in update_expr.mapping.items()]

            # if there is a non-zero constant in the update expression, include it in the list of terms to be summed
            if update_expr.const != 0:
                prod_vars.append(gen.make_const_real(update_expr.const))

            # add up all of these products
            sum_var = adder_tree(prod_vars,
                                 zero_func=lambda: gen.make_const_real(0),
                                 add_func=lambda a, b: gen.add_real(a, b))

            # update value of output
            gen.mem_into_real(sum_var, signal_name)

        # end module
        gen.end_module()
