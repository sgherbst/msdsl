from abc import ABC, abstractmethod
from typing import List
from numbers import Number

from msdsl.expr.signals import Signal
from msdsl.expr.expr import ModelExpr

class CodeGenerator(ABC):
    def __init__(self, filename=None, tab_string='    ', line_ending='\n', tmp_prefix='tmp'):
        # save settings
        self.filename = filename
        self.tab_string = tab_string
        self.line_ending = line_ending
        self.tmp_prefix = tmp_prefix

        # initialize variables
        self.tab_level = 0
        self.text = ''

    # concrete functions

    def indent(self):
        self.tab_level += 1

    def dedent(self):
        self.tab_level -= 1
        assert self.tab_level >= 0

    def write(self, string=''):
        self.text += string

    def println(self, line=''):
        self.write(self.tab_level*self.tab_string + line + self.line_ending)

    def dump_to_file(self):
        with open(self.filename, 'w') as f:
            f.write(self.text)

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
    def make_probe(self, s: Signal):
        pass

    @abstractmethod
    def set_this_cycle(self, signal: Signal, expr: ModelExpr):
        pass

    @abstractmethod
    def set_next_cycle(self, signal: Signal, expr: ModelExpr, init: Number):
        pass

    @abstractmethod
    def bind_name(self, name: str, expr: ModelExpr):
        pass

    @abstractmethod
    def start_module(self, name: str, ios: List[Signal]):
        pass

    @abstractmethod
    def end_module(self):
        pass

    @abstractmethod
    def compile_expr(self, expr):
        pass