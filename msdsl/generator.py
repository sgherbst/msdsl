from abc import ABC, abstractmethod
from numbers import Number
from typing import List

from msdsl.expr import Signal, DigitalSignal, AnalogSignal, Plus, Times, Constant, AnalogArray
from msdsl.util import tree_op

class CodeGenerator(ABC):
    def __init__(self, filename, tab_string='    ', line_ending='\n', tmp_prefix='tmp'):
        self.filename = filename
        self.tab_string = tab_string
        self.line_ending = line_ending
        self.tmp_prefix = tmp_prefix

        # initialize variables
        self.tab_level = 0
        self.tmp_counter = 0

    # concrete functions

    def tmp_name(self):
        name = f'{self.tmp_prefix}{self.tmp_counter}'
        self.tmp_counter += 1

        return name

    def indent(self):
        self.tab_level += 1

    def dedent(self):
        self.tab_level -= 1
        assert self.tab_level >= 0

    def write(self, string='', mode='a'):
        with open(self.filename, mode) as f:
            f.write(string)

    def println(self, line=''):
        self.write(self.tab_level*self.tab_string + line + self.line_ending)

    def clear(self):
        self.write(mode='w')

    ###############################
    # concrete methods
    ###############################

    def compile_expr(self, expr):
        if isinstance(expr, Number):
            return self.make_analog_const(expr)
        elif isinstance(expr, Signal):
            return expr
        elif isinstance(expr, Constant):
            return self.make_analog_const(expr.value)
        elif isinstance(expr, AnalogArray):
            # compile terms and address
            gen_terms = [self.compile_expr(term) for term in expr.terms]
            gen_addr = self.compile_expr(expr.addr)

            # implement the lookup table
            return self.make_analog_array(gen_terms, gen_addr)
        elif isinstance(expr, Plus):
            # compile each term
            gen_terms = [self.compile_expr(term) for term in expr.terms]

            # implement operations in a tree
            op = lambda a, b: self.make_plus(a, b)
            default = lambda: self.make_analog_const(0)
            return tree_op(gen_terms, op=op, default=default)
        elif isinstance(expr, Times):
            # compile each term
            terms = [self.compile_expr(term) for term in expr.terms]

            # implement operations in a tree
            op = lambda a, b: self.make_times(a, b)
            default = lambda: self.make_analog_const(1)
            return tree_op(terms, op=op, default=default)
        else:
            raise Exception('Invalid expression type.')

    ###############################
    # abstract methods
    ###############################

    @abstractmethod
    def make_section(self, label):
        pass

    @abstractmethod
    def make_signal(self, s: Signal):
        pass

    @abstractmethod
    def make_assign(self, input_: Signal, output: Signal):
        pass

    @abstractmethod
    def make_times(self, a: Signal, b: Signal) -> Signal:
        pass

    @abstractmethod
    def make_plus(self, a: Signal, b: Signal) -> Signal:
        pass

    @abstractmethod
    def make_mem(self, next: Signal, curr: Signal) -> Signal:
        pass

    @abstractmethod
    def make_analog_const(self, value: Number) -> AnalogSignal:
        pass

    @abstractmethod
    def make_analog_array(self, values: List[AnalogSignal], addr: DigitalSignal) -> AnalogSignal:
        pass

    @abstractmethod
    def start_module(self, name: str, ios: List[Signal]):
        pass

    @abstractmethod
    def end_module(self):
        pass