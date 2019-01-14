from abc import ABC, abstractmethod

class CodeGenerator(ABC):
    def __init__(self, filename, tab_string='    ', line_ending='\n', tmp_prefix='tmp'):
        self.filename = filename
        self.tab_string = tab_string
        self.line_ending = line_ending
        self.tmp_prefix = tmp_prefix

        # initialize variables
        self.tab_level = 0
        self.tmp_counter = 0
        self.namespace = set()

    # concrete functions

    def add_to_namespace(self, name):
        assert name not in self.namespace
        self.namespace.add(name)

    def tmpvar(self):
        """
        Returns a new variable name that doesn't conflict with any currently defined variables.
        """

        while True:
            name = f'{self.tmp_prefix}{self.tmp_counter}'
            self.tmp_counter += 1

            try:
                self.add_to_namespace(name)
            except AssertionError:
                continue
            else:
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

    # abstract methods

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
    def make_real(self, name, range):
        pass

    @abstractmethod
    def copy_format_real(self, input_, output):
        pass

    @abstractmethod
    def make_const_real(self, value):
        pass

    @abstractmethod
    def add_real(self, a, b):
        pass

    @abstractmethod
    def assign_real(self, input_, output):
        pass

    @abstractmethod
    def mem_into_real(self, next, curr):
        pass

    @abstractmethod
    def end_module(self):
        pass