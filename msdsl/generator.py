from abc import ABC, abstractmethod
from typing import List

from msdsl.expr import Signal

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
    def make_mem(self, next: Signal, curr: Signal) -> Signal:
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