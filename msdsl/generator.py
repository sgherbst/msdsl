from abc import ABC, abstractmethod

class CodeGenerator(ABC):
    @abstractmethod
    def start_module(self, name, inputs, outputs):
        pass

    @abstractmethod
    def section(self, label):
        pass

    @abstractmethod
    def mul_const_real(self, coeff, var):
        pass

    @abstractmethod
    def make_const_real(self, value):
        pass

    @abstractmethod
    def add_real(self, a, b):
        pass

    @abstractmethod
    def mem_into_real(self, next, curr):
        pass

    @abstractmethod
    def end_module(self):
        pass