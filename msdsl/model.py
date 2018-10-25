from itertools import chain
from numbers import Number
from msdsl.cpp import CppGen, ptr, deref

def listify(x):
    if isinstance(x, (list, tuple)):
        return x

    if isinstance(x, str):
        return [x]

    raise ValueError('Unknown input type: {}'.format(type(x)))

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
    def __init__(self, name, initial=None, type=None, expr=None):
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
        self.name = name
        self.initial = initial
        self.type = type
        self.expr = expr

class Model:
    def __init__(self, a_in=None, a_out=None, d_in=None, d_out=None, a_state=None, d_state=None,
                 name=None):

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
        if name is None:
            name = 'model'

        # make lists out of the arguments
        a_in = listify(a_in)
        a_out = listify(a_out)
        d_in = listify(d_in)
        d_out = listify(d_out)

        # save inputs
        self.a_in = [AnalogSignal(x) for x in a_in]
        self.d_in = [DigitalSignal(x) for x in d_in]
        self.a_out = [AnalogSignal(x) for x in a_out]
        self.d_out = [DigitalSignal(x) for x in d_out]
        self.a_state = [AnalogSignal(name=k, initial=v) for k,v in a_state.items()]
        self.d_state = [DigitalSignal(name=k, initial=v) for k,v in d_state.items()]
        self.name = name

        # add a timestep input
        self.dt = AnalogSignal('dt')
        self.a_in.insert(0, self.dt)

        # create name mapping
        self.mapping = {}
        for x in chain(self.a_in, self.d_in, self.a_out, self.d_out, self.a_state, self.d_state):
            self.mapping[x.name] = x

    def __getattr__(self, name):
        return self.mapping[name]

    def emit(self, target, cpp='model.cpp', hpp='model.hpp'):
        # make IO list
        io = []
        io += [(x.type, x.name) for x in self.a_in]
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

        # compute new state variables values in parallel
        gen.comment('Compute new state variables values in parallel')
        for x in self.a_state:
            gen.assign(lhs='{} {}'.format(x.type, x.tmpvar),
                       rhs='{}+({}*({}))'.format(x.name, self.dt.name, AnalogExpr.make(x.expr).to_cpp()))
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
