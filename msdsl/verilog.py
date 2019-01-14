class VerilogGenerator:
    def __init__(self, filename, tab_string='    ', line_ending='\n'):
        self.filename = filename
        self.tab_string = tab_string
        self.line_ending = line_ending

        # initialize variables
        self.tab_level = 0
        self.tmp_counter = 0

        # clear output file
        with open(self.filename, 'w') as f:
            f.write('')

    def tmpvar(self):
        retval = f'tmp{self.tmp_counter}'
        self.tmp_counter += 1
        return retval

    def timescale(self, unit='ns', precision='ps'):
        self.println(f'`timescale 1{unit}/1{precision}')

    def include(self, file):
        self.println(f'`include "{file}"')

    def comma_separated_lines(self, lines):
        if len(lines) == 0:
            pass
        elif len(lines) == 1:
            self.println(lines[0])
        else:
            self.println(lines[0] + ',')
            self.comma_separated_lines(lines[1:])

    def comment(self, content=''):
        self.println(f'// {content}')

    def indent(self):
        self.tab_level += 1

    def dedent(self):
        self.tab_level -= 1
        assert self.tab_level >= 0

    def println(self, line=''):
        with open(self.filename, 'a') as f:
            f.write(self.tab_level*self.tab_string + line + self.line_ending)

    def start_module(self, name, parameters=None, ios=None):
        # set defaults
        if parameters is None:
            parameters = []
        if ios is None:
            ios = []

        # module name
        self.println(f'module {name} #(')

        # parameters
        self.indent()
        self.comma_separated_lines(parameters)
        self.dedent()
        self.println(') (')

        # IO
        self.indent()

        self.comma_separated_lines(ios)
        self.dedent()
        self.println(');')

        # set indentation level
        self.indent()

    def end_module(self):
        self.dedent()
        self.println('endmodule')