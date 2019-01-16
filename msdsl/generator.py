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

    def compile_expr(self, expr):
        if isinstance(expr, Number):
            return self.make_analog_const(expr)
        elif isinstance(expr, Signal):
            return expr
        elif isinstance(expr, Constant):
            return self.make_analog_const(expr.value)
        elif isinstance(expr, AnalogArray):
            return self.make_analog_array(expr.values, self.compile_expr(expr.addr))
        elif isinstance(expr, Plus):
            gen_terms = [self.compile_expr(term) for term in expr.terms]

            # implement operations in a tree
            op = lambda a, b: self.make_plus(a, b)
            default = lambda: self.make_analog_const(0)
            return tree_op(gen_terms, op=op, default=default)
        elif isinstance(expr, Times):
            # run generator on terms
            terms = [self.compile_expr(term) for term in expr.terms]

            # implement operations in a tree
            op = lambda a, b: self.make_times(a, b)
            default = lambda: self.make_analog_const(1)
            return tree_op(terms, op=op, default=default)

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
    def make_analog_array(self, values: List[Number], addr: DigitalSignal) -> AnalogSignal:
        pass

    @abstractmethod
    def start_module(self, name: str, ios: List[Signal]):
        pass

    @abstractmethod
    def end_module(self):
        pass

# unused optimized code

# def times(terms: List[ModelExpr]):
#     # consolidate products
#     new_terms = []
#     for term in terms:
#         if isinstance(term, Times):
#             new_terms.extend(term.terms)
#         else:
#             new_terms.append(term)
#     terms = new_terms
#
#     # consolidate constants
#     other_terms = []
#     const_product = 1
#     for term in terms:
#         if isinstance(term, Constant):
#             const_product *= term.value
#         else:
#             other_terms.append(term)
#     terms = other_terms
#
#     if const_product == 0:
#         return Constant(0)
#     elif const_product != 1:
#         terms.append(Constant(const_product))
#
#     # when two items are multiplied together and one is a constant, make sure the constant comes first (to
#     # simplify subsequent processing)
#     if len(terms)==2 and isinstance(terms[0], Constant):
#         return const_times(terms[0], terms[1])
#     elif len(terms)==2 and isinstance(terms[1], Constant):
#         return const_times(terms[1], terms[0])
#     else:
#         return Times(terms)

# def plus(terms: List[ModelExpr]):
#     # consolidate sums
#     new_terms = []
#     for term in terms:
#         if isinstance(term, Plus):
#             new_terms.extend(term.terms)
#         else:
#             new_terms.append(term)
#     terms = new_terms
#
#     # consolidate constants
#     other_terms = []
#     const_sum = 0
#     for term in terms:
#         if isinstance(term, Constant):
#             const_sum += term.value
#         else:
#             other_terms.append(term)
#     terms = other_terms
#
#     if const_sum != 0:
#         terms.append(Constant(const_sum))
#
#     # group terms
#     other_terms = []
#     coeff_dict = {}
#
#     for term in terms:
#         if isinstance(term, Signal):
#             name = term.name
#             coeff = 1
#         elif isinstance(term, ConstTimes) and isinstance(term.expr, Signal):
#             name = term.expr.name
#             coeff = term.coeff.value
#         else:
#             other_terms.append(term)
#             continue
#
#         if name not in coeff_dict:
#             coeff_dict[name] = 0
#         coeff_dict[name] += coeff
#
#     terms = other_terms
#
#     for name, coeff in coeff_dict.items():
#         terms.append(coeff*Signal(name))
#
#     return Plus(terms)