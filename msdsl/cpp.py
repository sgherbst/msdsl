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

def gt(a, b):
    return str(a) + ' > ' + str(b)

def ge(a, b):
    return str(a) + ' >= ' + str(b)

def lt(a, b):
    return str(a) + ' < ' + str(b)

def le(a, b):
    return str(a) + ' <= ' + str(b)

def const(type_):
    return 'const ' + type_

class CppGen:
    def __init__(self, tab='    ', newline='\n'):
        self.tab = tab
        self.newline = newline

        self.level = 0
        self.line_started = False

    def indent(self):
        self.level += 1

    def dedent(self):
        self.level -= 1

    def include(self, f):
        self.print('#include ' + f)

    def typedef(self, type_, name):
        self.print('typedef ' + type_ + ' ' + name + ';')

    def assign(self, lhs, rhs):
        self.print(lhs + ' = ' + rhs + ';')

    def start_function(self, func_type, func_name, io):
        arg_list = ', '.join(arg_type + ' ' + arg_name for arg_type, arg_name in io)
        self.print(func_type + ' ' + func_name + '(' + arg_list + ') {')
        self.indent()

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
            print(self.tab*self.level, end='')
            self.line_started = True

        print(s, end='')

        if newline:
            print(self.newline, end='')
            self.line_started = False