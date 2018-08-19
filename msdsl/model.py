from sympy import linear_eq_to_matrix


class AnalogSignal:
    def __init__(self, name=None, range_=None, rel_tol=None, abs_tol=None, expr=None, initial=None):
        # set defaults
        if (rel_tol is None) and (abs_tol is None):
            rel_tol = 5e-7

        # save settings
        self.name = name
        self.range_ = range_
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol
        self.expr = expr
        self.initial = initial


class DigitalSignal:
    def __init__(self, name=None, signed=None, width=None, expr=None, initial=None):
        # set defaults
        if signed is None:
            signed = False
        if width is None:
            width = 1

        self.name = name
        self.signed = signed
        self.width = width
        self.expr = expr
        self.initial = initial


class CaseCoeffProduct:
    def __init__(self, var=None, num_cases=None, coeffs=None):
        # set defaults
        if num_cases is not None:
            assert coeffs is None
            coeffs = [0]*num_cases
        else:
            assert coeffs is not None
            num_cases = len(coeffs)

        # save settings
        self.var = var
        self.num_cases = num_cases
        self.coeffs = coeffs

    def update(self, case_no, coeff):
        self.coeffs[case_no] = coeff


class CaseLinearExpr:
    def __init__(self, num_cases=None, prods=None, const=None):
        # set defaults
        if num_cases is not None:
            assert prods is None
            prods = []

            assert const is None
            const = CaseCoeffProduct(num_cases=num_cases)
        else:
            assert (prods is not None) and (const is not None)
            num_cases = const.num_cases

        # save settings
        self.num_cases = num_cases
        self.const = const

        # dictionary mapping variable names to the associated CaseCoeffProduct object
        self._var_dict = {prod.var: prod for prod in prods}

    @property
    def prods(self):
        return list(self._var_dict.values())

    def get_var(self, var):
        return self._var_dict[var]

    def has_var(self, var):
        return var in self._var_dict

    def init_var(self, var):
        prod = CaseCoeffProduct(var=var, num_cases=self.num_cases)

        self._var_dict[var] = prod
        self.prods.append(prod)

        return prod

    def add_case(self, case_no, expr):
        # convert symbolic expression to a linear form
        syms = list(expr.free_symbols)
        A, b = linear_eq_to_matrix([expr], syms)

        # get coefficient values and variable names
        coeffs = [float(x) for x in A]
        vars = [sym.name for sym in syms]

        # update coeff products
        for coeff, var in zip(coeffs, vars):
            if not self.has_var(var):
                self.init_var(var)
            self.get_var(var).update(case_no, coeff)

        # update constant
        self.const.update(case_no, -float(b[0]))


class MixedSignalModel:
    def __init__(self, analog_inputs=None, digital_inputs=None, analog_outputs=None, digital_outputs=None,
                 analog_states=None, digital_states=None, mode=None):

        # initialize model
        self.analog_inputs = []
        self.digital_inputs = []
        self.analog_outputs = []
        self.digital_outputs = []
        self.analog_states = []
        self.digital_states = []
        self.mode = []

        # initial name dictionary
        self._signal_name_dict = {}

        # apply inputs
        if analog_inputs is not None:
            self.add_analog_inputs(analog_inputs)
        if digital_inputs is not None:
            self.add_digital_inputs(digital_inputs)
        if analog_outputs is not None:
            self.add_analog_outputs(analog_outputs)
        if digital_outputs is not None:
            self.add_digital_outputs(digital_outputs)
        if analog_states is not None:
            self.add_analog_states(analog_states)
        if digital_states is not None:
            self.add_digital_states(digital_states)
        if mode is not None:
            self.mode = mode

    # get specific I/O by name

    def get_signal(self, name):
        return self._signal_name_dict[name]

    def has_signal(self, name):
        return name in self._signal_name_dict

    def add_signals(self, *args):
        for arg in args:
            assert not self.has_signal(arg.name)
            self._signal_name_dict[arg.name] = arg

    # Build model

    def add_analog_inputs(self, *args):
        self.analog_inputs.extend(args)
        self.add_signals(*args)
        
    def add_digital_inputs(self, *args):
        self.digital_inputs.extend(args)
        self.add_signals(*args)

    def add_analog_outputs(self, *args):
        self.analog_outputs.extend(args)
        self.add_signals(*args)

    def add_digital_outputs(self, *args):
        self.digital_outputs.extend(args)
        self.add_signals(*args)

    def add_analog_states(self, *args):
        self.analog_states.extend(args)
        self.add_signals(*args)

    def add_digital_states(self, *args):
        self.digital_states.extend(args)
        self.add_signals(*args)