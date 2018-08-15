from sympy import linear_eq_to_matrix

class CaseLinearExpr:
    def __init__(self, num_cases, coeffs=None, const=None):
        # set defaults
        if coeffs is None:
            coeffs = {}
        if const is None:
            const = [None] * num_cases

        self.num_cases = num_cases
        self.coeffs = coeffs
        self.const = const

    def add_case(self, case_no, expr):
        syms = list(expr.free_symbols)
        sym_names = [sym.name for sym in syms]

        A, b = linear_eq_to_matrix([expr], syms)

        # add variables
        vars = [float(x) for x in A]
        for sym_name, var in zip(sym_names, vars):
            if sym_name not in self.coeffs:
                self.coeffs[sym_name] = [None] * self.num_cases
            self.coeffs[sym_name][case_no] = var

        # add constant
        self.const[case_no] = -float(b[0])

    def to_dict(self):
        return vars(self)

    @staticmethod
    def from_dict(d):
        return CaseLinearExpr(**d)

class MixedSignalModel:
    def __init__(self, analog_inputs=None, digital_inputs=None, mode=None, analog_outputs=None, analog_states=None,
                 digital_states=None):

        self.analog_inputs = []
        self.digital_inputs = []
        self.mode = None
        self.analog_outputs = {}
        self.analog_states = {}
        self.digital_states = {}

        if analog_inputs is not None:
            self.add_analog_inputs(analog_inputs)
        if digital_inputs is not None:
            self.add_digital_inputs(digital_inputs)
        if mode is not None:
            self.define_mode(mode)
        if analog_outputs is not None:
            self.add_analog_outputs(analog_outputs)
        if analog_states is not None:
            self.add_analog_states(analog_states)
        if digital_states is not None:
            self.add_digital_states(digital_states)

    def add_analog_inputs(self, analog_inputs):
        self.analog_inputs.extend(analog_inputs)

    def add_digital_inputs(self, digital_inputs):
        self.digital_inputs.extend(digital_inputs)

    def define_mode(self, mode):
        self.mode = mode

    def add_analog_outputs(self, analog_outputs):
        self.analog_outputs.update(analog_outputs)

    def add_analog_states(self, analog_states):
        self.analog_states.update(analog_states)

    def add_digital_states(self, digital_state):
        self.digital_states.update(digital_state)

    def to_dict(self):
        d = vars(self)
        d['analog_outputs'] = {key: val.to_dict() for key, val in d['analog_outputs'].items()}
        d['analog_states'] = {key: val.to_dict() for key, val in d['analog_states'].items()}
        d['digital_states'] = {key: val.to_dict() for key, val in d['digital_states'].items()}

        return d

    @staticmethod
    def from_dict(d):
        d_copy = d.copy()

        d_copy['analog_outputs'] = {key: CaseLinearExpr.from_dict(val)
                                    for key, val in d_copy['analog_outputs'].items()}
        d_copy['analog_states'] = {key: CaseLinearExpr.from_dict(val)
                                   for key, val in d_copy['analog_states'].items()}
        d_copy['digital_states'] = {key: CaseLinearExpr.from_dict(val)
                                    for key, val in d_copy['digital_states'].items()}

        return MixedSignalModel(**d)

# from interval import interval
#
# class AnalogSignal:
#     def __init__(self, name=None, range_=None, rel_tol=None, abs_tol=None):
#         # set defaults
#         if range_ is None:
#             range_ = interval[-1, 1]
#         if (rel_tol is None) and (abs_tol is None):
#             rel_tol = 1e-3
#
#         # compute tolerance
#         if rel_tol is not None:
#             assert abs_tol is None, 'Cannot specify both relative and absolute tolerance.'
#             abs_tol = rel_tol * max(abs(range_[0].inf), abs(range_[0].sup))
#
#         # save settings
#         self.name = name
#         self.range_ = range_
#         self.abs_tol = abs_tol
#
#     def to_dict(self):
#         d = vars(self)
#         d['range_'] = [self.range_[0].inf, self.range_[0].sup]
#
#         return d
#
#     @staticmethod
#     def from_dict(d):
#         d_copy = d.copy()
#         d_copy['range_'] = interval[d_copy['range_'][0], d_copy['range_'][1]]
#
#         return AnalogSignal(**d_copy)
#
# class DigitalSignal:
#     def __init__(self, name=None, signed=False, width=1):
#         self.name = name
#         self.signed = signed
#         self.width = width
#
#     def to_dict(self):
#         return vars(self)
#
#     @staticmethod
#     def from_dict(d):
#         return DigitalSignal(**d)
#
# class ModeVariable:
#     def __init__(self, name=None, concatenation=None):
#         self.