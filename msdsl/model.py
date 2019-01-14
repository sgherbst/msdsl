from numbers import Number
from scipy.signal import cont2discrete
from collections import OrderedDict
from itertools import chain

from msdsl.generator import CodeGenerator
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
        self.signals = {}
        for signal in inputs+outputs:
            self.add_signal(signal)

        # internal variables
        self.internal_variables = OrderedDict()

        # expressions used to assign internal and external signals
        self.next_cycle = OrderedDict()
        self.this_cycle = OrderedDict()

    def __getattr__(self, item):
        return self.signals[item]

    def add_signal(self, name):
        self.signals[name] = self.sig2expr(name)

    def add_internal_variable(self, name, range):
        self.internal_variables[name] = range
        self.add_signal(name)

    def set_deriv(self, name, expr):
        self.next_cycle[name] = self.dt*expr + self.signals[name]

    def set_tf(self, output, input_, tf):
        # discretize transfer function
        res = cont2discrete(tf, self.dt)

        # get numerator and denominator coefficients
        b = [+float(val) for val in res[0].flatten()]
        a = [-float(val) for val in res[1].flatten()]

        # create input and output histories
        i_hist = self.make_history(input_, len(b))
        o_hist = self.make_history(output, len(a))

        # implement the filter
        expr = LinearExpr()
        for coeff, var in chain(zip(b, i_hist), zip(a[1:], o_hist)):
            expr += coeff*var

        self.next_cycle[output] = expr

    def make_history(self, first, length):
        hist = []

        for k in range(length):
            if k == 0:
                hist.append(self.signals[first])
            else:
                curr = f'{first}_{k}'
                self.add_internal_variable(curr, first)
                self.next_cycle[curr] = hist[k-1]
                hist.append(self.signals[curr])

        return hist

    def run_generator(self, gen: CodeGenerator):
        # start module
        gen.start_module(name=self.name, inputs=self.inputs, outputs=self.outputs)

        # create internal variables
        gen.section('Defining internal variables')
        for var_name, var_range in self.internal_variables.items():
            if isinstance(var_range, Number):
                gen.make_real(var_name, var_range)
            elif isinstance(var_name, str):
                gen.copy_format_real(var_range, var_name)
            else:
                raise Exception('Invalid range type for internal variable.')

        # update values of variables for the next cycle
        for signal_name, next_expr in self.next_cycle.items():
            # label this section of the code for debugging purposes
            gen.section(f'Updating signal: {signal_name}')

            # implement the update expression
            result = next_expr.run_generator(gen)
            gen.mem_into_real(result, signal_name)

        # update values of variables for the current cycle
        for signal_name, this_expr in self.this_cycle.items():
            # label this section of the code for debugging purposes
            gen.section(f'Assigning signal: {signal_name}')

            # implement the update expression
            result = this_expr.run_generator(gen)
            gen.assign_real(result, signal_name)

        # end module
        gen.end_module()

    # utility functions

    @staticmethod
    def sig2expr(sig):
        return LinearExpr({sig: 1.0})