def generic(type_, *args):
    return type_ + '<' + ', '.join(str(arg) for arg in args) + '>'

def ap_int(*args):
    return generic('ap_int', *args)

def ap_uint(*args):
    return generic('ap_uint', *args)

def ap_fixed(*args):
    return generic('ap_fixed', *args)

def ap_ufixed(*args):
    return generic('ap_ufixed', *args)

def ptr(type_):
    return type_ + '*'

def deref(var):
    return '*' + var

def parens(expr):
    return '(' + expr + ')'

def concat(*args):
    return '(' + ', '.join(str(arg) for arg in args) + ')'

def instance(type_, *args):
    return type_ + concat(*args)

def const(type_):
    return 'const ' + type_

class CppGen:
    def __init__(self, filename=None, tab='    ', newline='\n'):
        self.filename = filename
        self.tab = tab
        self.newline = newline

        self.level = 0
        self.line_started = False

        self.clear()

    def indent(self):
        self.level += 1

    def dedent(self):
        self.level -= 1

    def include(self, f):
        self.print('#include ' + f)

    def define(self, macro_name, macro_definition):
        self.print('#define ' + macro_name + ' ' + macro_definition)

    def start_include_guard(self, var):
        self.print('#ifndef ' + var)
        self.print('#define ' + var)

    def end_include_guard(self, var):
        self.print('#endif // ' + var)

    def typedef(self, type_, name):
        self.print('typedef ' + type_ + ' ' + name + ';')

    def assign(self, lhs, rhs):
        self.print(lhs + ' = ' + rhs + ';')

    def start_function(self, func_type, func_name, io):
        arg_list = ', '.join(arg_type + ' ' + arg_name for arg_type, arg_name in io)
        self.print(func_type + ' ' + func_name + '(' + arg_list + ') {')
        self.indent()

    def function_prototype(self, func_type, func_name, io):
        arg_list = ', '.join(arg_type + ' ' + arg_name for arg_type, arg_name in io)
        self.print(func_type + ' ' + func_name + '(' + arg_list + ');')

    def end_function(self):
        self.dedent()
        self.print('}')

    def static(self, type_, name, initial=None):
        self.print('static ' + type_ + ' ' + name, newline=False)
        if initial is not None:
            self.print(' = ' + str(initial), newline=False)
        self.print(';')

    def comment(self, s):
        self.print('// ' + s)

    def array(self, type_, name, values):
        literal = '{' + ', '.join(str(x if (x != 0) else 0) for x in values) + '}'
        self.print(type_ + ' ' + name + ' [] = ' + literal + ';')

    def print(self, s='', newline=True):
        if not self.line_started:
            self.write(self.tab*self.level)
            self.line_started = True

        self.write(s)

        if newline:
            self.write(self.newline)
            self.line_started = False

    def clear(self):
        with open(self.filename, 'w') as f:
            f.write('')

    def write(self, data):
        with open(self.filename, 'a') as f:
            f.write(data)