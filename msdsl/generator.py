from abc import ABC, abstractmethod
from numbers import Number
from typing import List

from msdsl.expr import (Signal, DigitalSignal, AnalogSignal, Plus, Times, Constant, AnalogArray, BinaryOp, ListOp,
                        LessThan, LessThanOrEquals, GreaterThan, GreaterThanOrEquals, Concatenate, EqualTo,
                        NotEqualTo)
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
        elif isinstance(expr, ListOp):
            # compile each term
            gen_terms = [self.compile_expr(term) for term in expr.terms]

            # determine the elementwise operations
            if isinstance(expr, Plus):
                op = lambda a, b: self.make_plus(a, b)
                default = lambda: self.make_analog_const(0)
            elif isinstance(expr, Times):
                op = lambda a, b: self.make_times(a, b)
                default = lambda: self.make_analog_const(1)
            else:
                raise Exception('Invalid ListOp type.')

            # implement operations in a tree
            return tree_op(gen_terms, op=op, default=default)
        elif isinstance(expr, BinaryOp):
            gen_lhs = self.compile_expr(expr.lhs)
            gen_rhs = self.compile_expr(expr.rhs)

            if isinstance(expr, LessThan):
                return self.make_less_than(gen_lhs, gen_rhs)
            elif isinstance(expr, LessThanOrEquals):
                return self.make_less_than_or_equals(gen_lhs, gen_rhs)
            elif isinstance(expr, GreaterThan):
                return self.make_greater_than(gen_lhs, gen_rhs)
            elif isinstance(expr, GreaterThanOrEquals):
                return self.make_greater_than_or_equals(gen_lhs, gen_rhs)
            elif isinstance(expr, EqualTo):
                return self.make_equal_to(gen_lhs, gen_rhs)
            elif isinstance(expr, NotEqualTo):
                return self.make_not_equal_to(gen_lhs, gen_rhs)
            else:
                raise Exception('Invalid BinaryOp type.')
        elif isinstance(expr, Concatenate):
            gen_terms = [self.compile_expr(term) for term in expr.terms]
            return self.make_concatenate(gen_terms)
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
    def make_less_than(self, lhs, rhs):
        pass

    @abstractmethod
    def make_less_than_or_equals(self, lhs, rhs):
        pass

    @abstractmethod
    def make_greater_than(self, lhs, rhs):
        pass

    @abstractmethod
    def make_greater_than_or_equals(self, lhs, rhs):
        pass

    @abstractmethod
    def make_equal_to(self, lhs, rhs):
        pass

    @abstractmethod
    def make_not_equal_to(self, lhs, rhs):
        pass

    @abstractmethod
    def make_concatenate(self, terms: List[DigitalSignal]) -> DigitalSignal:
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