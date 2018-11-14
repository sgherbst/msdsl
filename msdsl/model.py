from itertools import chain
from numbers import Number
from msdsl.cpp import CppGen, ptr, deref
from msdsl.util import listify

class CoeffPair:
    def __init__(self, coeff, signal):
        self.coeff = coeff
        self.signal = signal

    def __add__(self, other):
        assert self.signal.name == other.signal.name
        return CoeffPair(self.coeff + other.coeff, other.signal)

    __radd__ = __add__

    def __sub__(self, other):
        return (self + (-1.0*other))

    __rsub__ = __sub__

    def __mul__(self, other):
        assert isinstance(other, Number)
        return CoeffPair(coeff=other*self.coeff, signal=self.signal)

    __rmul__ = __mul__

    def __truediv__(self, other):
        assert isinstance(other, Number)
        return self*(1.0/other)

    __rtruediv__ = __truediv__

    def to_cpp(self):
        if self.coeff == 0:
            return None

        if self.coeff == 1:
            return self.signal.name

        return '({}*{})'.format(self.coeff, self.signal.name)

class AnalogExpr:
    def __init__(self, signals=None, constant=None):
        # set defaults
        if signals is None:
            signals = {}
        if constant is None:
            constant = 0

        # save settings
        self.signals = signals
        self.constant = constant

    def to_cpp(self):
        terms = [x.to_cpp() for x in self.signals.values()]
        terms = [x for x in terms if x is not None]
        if self.constant != 0:
            terms += str(self.constant)

        if len(terms) > 0:
            return '+'.join(terms)
        else:
            return '0'

    @staticmethod
    def make(x):
        if isinstance(x, AnalogExpr):
            return x
        if isinstance(x, AnalogSignal):
            return AnalogExpr(signals={x.name: CoeffPair(coeff=1, signal=x)})
        if isinstance(x, Number):
            return AnalogExpr(signals={}, constant=x)

        raise ValueError('Cannot make AnalogExpr from {}'.format(type(x)))

    def __add__(self, other):
        other = AnalogExpr.make(other)

        # determine new signal dictionary
        new_signals = {}
        for name, coeff_pair in chain(self.signals.items(), other.signals.items()):
            if name not in new_signals:
                new_signals[name]  = coeff_pair
            else:
                new_signals[name] += coeff_pair

        # determine new constant
        new_constant = self.constant+other.constant

        # return new expression
        return AnalogExpr(signals=new_signals, constant=new_constant)

    __radd__ = __add__

    def __sub__(self, other):
        other = AnalogExpr.make(other)
        return (self + (-1.0*other))

    __rsub__ = __sub__

    def __mul__(self, other):
        other = AnalogExpr.make(other)

        if len(self.signals) > 0:
            if len(other.signals) > 0:
                raise ValueError('Nonlinear terms not allowed yet.')
            else:
                orig_signals = self.signals.copy()

            mul_by = other.constant
        else:
            if len(other.signals) > 0:
                orig_signals = other.signals.copy()
            else:
                orig_signals = {}

            mul_by = self.constant

        new_signals = {name: mul_by*coeff_pair for name, coeff_pair in orig_signals.items()}
        new_constant = self.constant * other.constant

        return AnalogExpr(signals=new_signals, constant=new_constant)

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = AnalogExpr.make(other)
        assert len(other.signals) == 0

        return (self * (1.0/other.constant))

    __rtruediv__ = __truediv__

class AnalogSignal:
    def __init__(self, name, initial=None, type=None, expr={}):
        # set defaults
        if type is None:
            type = 'float'

        self.name = name
        self.initial = initial
        self.type = type
        self.expr = expr

    @property
    def tmpvar(self):
        return 'tmp_' + self.name

    def __add__(self, other):
        return (AnalogExpr.make(self) + AnalogExpr.make(other))

    __radd__ = __add__

    def __sub__(self, other):
        return (AnalogExpr.make(self) - AnalogExpr.make(other))

    __rsub__ = __sub__

    def __mul__(self, other):
        return (AnalogExpr.make(self) * AnalogExpr.make(other))

    __rmul__ = __mul__

    def __truediv__(self, other):
        return (AnalogExpr.make(self) / AnalogExpr.make(other))

    __rtruediv__ = __truediv__

class DigitalSignal:
    def __init__(self, name, initial=None, type=None, expr=None):
        # set defaults
        if type is None:
            type = 'int'

        self.name = name
        self.initial = initial
        self.type = type
        self.expr = expr

# TODO I think we can delete this
# A list of operating modes and rules for choosing which mode every cycle
class OperatingModes:
    def __init__(self, name, modes):
        self.name = name
        self.components = {}

# Nodes are boolean expressions or switch-case things, leaves are operating modes or decision trees
class DecisionTree:
    def __init__(self, boolean=None, children=None):
        if boolean != None:
            if len(children) != 2:
                raise ValueError('DecisionTree with boolean expression must have 2 children')
            self.boolean = boolean
            self.children = children
        else:
            raise NotImplementedError('Decision tree only supports boolean decisions for now')

class Model:
    def __init__(self, a_in=None, a_out=None, d_in=None, d_out=None, a_state=None, d_state=None,
                 modes=None, name=None):

        # set defaults
        if a_in is None:
            a_in = []
        if a_out is None:
            a_out = []
        if d_in is None:
            d_in = []
        if d_out is None:
            d_out = []
        if a_state is None:
            a_state = {}
        if d_state is None:
            d_state = {}
        if modes is None:
            modes = {}
        if name is None:
            name = 'model'

        # make lists out of the arguments
        a_in = listify(a_in, str)
        a_out = listify(a_out, str)
        d_in = listify(d_in, str)
        d_out = listify(d_out, str)

        # save inputs
        self.a_in = [AnalogSignal(x) for x in a_in]
        self.d_in = [DigitalSignal(x) for x in d_in]
        self.a_out = [AnalogSignal(x) for x in a_out]
        self.d_out = [DigitalSignal(x) for x in d_out]
        self.a_state = [AnalogSignal(name=k, initial=v) for k,v in a_state.items()]
        self.d_state = [DigitalSignal(name=k, initial=v) for k,v in d_state.items()]
        # TODO copy modes
        self.modes = {}
        self.name = name

        # add a timestep input
        self.dt = AnalogSignal('dt')
        self.a_in.insert(0, self.dt)

        # create name mapping
        self.mapping = {}
        for x in chain(self.a_in, self.d_in, self.a_out, self.d_out, self.a_state, self.d_state, self.modes):
            self.mapping[x.name] = x

    def __getattr__(self, name):
        return self.mapping[name]

    # shorthand for adding a operating mode depending on digital input(s)
    def digital_dependence(self, digital, name=None):
        inputs = listify(digital, str)
        digital_names = [d.name for d in self.d_in]
        for d in inputs:
            if d not in digital_names:
                raise ValueError('digital_dependence signal "%s" is not a digital input'%d)

        if name is None:
            name = ','.join(inputs)
        num_bits = len(inputs)
        codes = []
        def aux(depth, code):
            if depth == num_bits:
                codes.append(code)
                return code
            sig = inputs[depth]
            f = aux(depth+1, code+'0')
            t = aux(depth+1, code+'1')
            return DecisionTree(boolean=sig, children=[f,t])
        tree = aux(0, name+':')
        codes = tuple(codes) # we don't want to give the client somethign mutable
        self.modes[name] = (tree, codes)
        return codes

    # so that the user does not need to worry about ordering of modes when defining expressions
    def clean_modes(self):
        for state in self.a_state:
            if type(state) == AnalogSignal:
                continue
            expr_clean = {}
            for k in state:
                expr_clean[sorted(k)] = state.expr[k]
            state.expr = expr_clean

    def emit(self, target, cpp='model.cpp', hpp='model.hpp'):
        # make IO list
        io = []
        io += [(x.type, x.name) for x in self.a_in]
        io += [(x.type, x.name) for x in self.d_in]
        io += [(ptr(x.type), x.name) for x in self.a_out]

        # write header file
        gen = CppGen(hpp)
        include_guard_var = '__' + hpp.upper().replace('.', '_') + '__'
        gen.start_include_guard(include_guard_var)
        gen.print()
        gen.function_prototype('void', self.name, io)
        gen.print()
        gen.end_include_guard(include_guard_var)

        # write main program
        gen = CppGen(cpp)

        # start function
        gen.start_function('void', self.name, io=io)

        # initialize state variables
        gen.comment('Initialize state variables')
        for x in self.a_state:
            gen.static(x.type, x.name, x.initial)
        gen.print()

        # decide on operating modes
        gen.comment('Decide on operating modes')
        # alphabetize lists of modes in keys to statevar.expr
        self.clean_modes()
        # TODO it would be nice if this counter were an enum with the same names as the codes
        code_map = {name:{} for name in self.modes}
        operating_state_var = 'operating_modes'
        # TODO: don't use gen.print for this, maybe make a gen.declare?
        gen.print('int {}[{}];'.format(operating_state_var, len(self.modes)))
        mode_names = sorted(list(self.modes)) # the order of these names decides their order in operating_state_var array
        for i, mode_name in enumerate(mode_names):
            t, code_names = self.modes[mode_name]
            code_counter = 0
            def traverse_tree(t):
                if type(t) == DecisionTree:
                    nonlocal code_counter
                    # only supports boolen for now
                    case = t.boolean
                    gen.start_if(case)
                    traverse_tree(t.children[0])
                    gen.add_else()
                    traverse_tree(t.children[1])
                    gen.end_if()
                else:
                    # we've reached a leaf, t is actually a string, a code given to the user to tag a coresponding expression
                    gen.assign(lhs = '{}[{}]'.format(operating_state_var, i),
                               rhs = '{}'.format(code_counter))
                    code_map[mode_name][code_counter] = t
                    code_counter += 1
            traverse_tree(t)
        gen.print()

        # compute new state variables values in parallel
        gen.comment('Compute new state variables values in parallel')

        for state_var in self.a_state:
            gen.print('{} {};'.format(state_var.type, state_var.tmpvar))

        # utility function for recursively creating tree of switch cases on various modes
        def switch_case_on_mode(unused_modes, used_mode_cases):
            if len(unused_modes) == 0:
                # emit expressions for each state var under modes in used_mode_cases
                for state_var in self.a_state:
                    if type(state_var.expr) == dict:
                        # this key expression is ugly, but it has to do with the way the client specifies codes
                        key = tuple(used_mode_cases) if len(used_mode_cases) > 1 else used_mode_cases[0]
                        expr = state_var.expr[key]
                    else:
                        expr = state_var.expr
                    gen.assign(lhs='{}'.format(state_var.tmpvar),
                               rhs='{}+({}*({}))'.format(state_var.name, self.dt.name, AnalogExpr.make(expr).to_cpp()))

            else:
                # continue making tree of switch cases
                mode = unused_modes[0]
                new_unused_modes = unused_modes[1:]
                mode_num = mode_names.index(mode)
                gen.start_switch_case('{}[{}]'.format(operating_state_var, mode_num))
                for code in sorted(list(code_map[mode])):
                    gen.start_case(str(code))
                    switch_case_on_mode(new_unused_modes, used_mode_cases+[code_map[mode][code]])
                    gen.end_case()
                gen.end_switch_case()

        switch_case_on_mode(mode_names, [])
        gen.print()

        # assign new state values in parallel
        gen.comment('Assign new state values in parallel')
        for x in self.a_state:
            gen.assign(lhs=x.name, rhs=x.tmpvar)
        gen.print()

        # assign output values in parallel
        gen.comment('Assign output values in parallel')
        for x in self.a_out:
            gen.assign(lhs=deref(x.name), rhs=AnalogExpr.make(x.expr).to_cpp())

        # end function
        gen.end_function()
