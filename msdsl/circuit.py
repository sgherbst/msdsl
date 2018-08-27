from sympy import solve, symbols
import logging

from msdsl.components import *
from msdsl.model import *
from msdsl.util import Namespace, SymbolNamespace, all_combos


class NodalAnalysis:
    def __init__(self):
        self.kcl = {}
        self.other_equations = []

    def set_equal(self, lhs, rhs):
        self.other_equations.append(lhs - rhs)

    def add_current(self, p, n, expr):
        self.kcl[p] = self.kcl.get(p, 0) - expr
        self.kcl[n] = self.kcl.get(n, 0) + expr


class DiodeExpr(DigitalExpr):
    def __init__(self, num_cases, mode):
        self.voltage = CaseLinearExpr(num_cases=num_cases, mode=mode)
        super().__init__(data='~', children=[DigitalExpr(data=self.voltage)])


class Circuit:
    def __init__(self):
        self.model = MixedSignalModel()

        self.symbol_namespace = SymbolNamespace()
        self.device_namespace = Namespace()

        self.linear_components = []
        self.diodes = []
        self.mosfets = []

        self.inductors = {}
        self.derivatives = {}

        self.output_symbols = {}

    def input_(self, name, range_=None, rel_tol=None, abs_tol=None):
        if range_ is None:
            range_ = [-10, 10]

        self.model.add_analog_inputs(AnalogSignal(name=name, range_=range_, rel_tol=rel_tol, abs_tol=abs_tol))

        return self.symbol_namespace.make(name)

    def output(self, sym, name=None, rel_tol=None, abs_tol=None):
        if name is None:
            name = sym.name

        self.output_symbols[name] = sym
        self.model.add_analog_outputs(AnalogSignal(name=name, rel_tol=rel_tol, abs_tol=abs_tol))

    def state(self, variable_name, derivative_name, range_=None, rel_tol=None, abs_tol=None, initial=None):
        signal = AnalogSignal(name=variable_name, range_=range_, rel_tol=rel_tol, abs_tol=abs_tol, initial=initial)
        self.model.add_analog_states(signal)

        variable = self.symbol_namespace.make(variable_name)
        derivative = self.symbol_namespace.make(derivative_name)

        self.derivatives[variable] = derivative

        return variable, derivative

    def symbols(self, *args):
        retval = []

        for arg in args:
            retval.append(self.symbol_namespace.make(arg))

        if len(retval) == 1:
            return retval[0]
        else:
            return retval

    def nodes(self, *args):
        return self.symbols(*args)

    def voltage_source(self, p, n, expr=None, name=None):
        name = self.device_namespace.make(name=name, prefix=VoltageSource.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        voltage_source = VoltageSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)
        self.linear_components.append(voltage_source)

        return voltage_source

    def current_source(self, p, n, expr=None, name=None):
        name = self.device_namespace.make(name=name, prefix=CurrentSource.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        current_source = CurrentSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)
        self.linear_components.append(current_source)

        return current_source

    def resistor(self, p, n, value, name=None):
        name = self.device_namespace.make(name=name, prefix=Resistor.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        resistor = Resistor(port=Port(p=p, n=n, v=v, i=i), value=value, name=name)
        self.linear_components.append(resistor)

        return resistor

    def inductor(self, p, n, value, name=None, range_=None, rel_tol=None, abs_tol=None, initial=None):
        # set defaults
        if range_ is None:
            range_ = [-25, 25]
        if initial is None:
            initial = 0

        name = self.device_namespace.make(name=name, prefix=Inductor.prefix)
        v = self.symbols('v_' + name)
        i, di_dt = self.state('i_' + name, 'di_dt_' + name, range_=range_, rel_tol=rel_tol, abs_tol=abs_tol,
                              initial=initial)

        inductor = Inductor(port=Port(p=p, n=n, v=v, i=i), di_dt=di_dt, value=value, name=name)
        self.linear_components.append(inductor)
        self.inductors[name] = inductor

        return inductor

    def capacitor(self, p, n, value, name=None, range_=None, rel_tol=None, abs_tol=None, initial=None):
        # set defaults
        if range_ is None:
            range_ = [-2e3, 2e3]
        if initial is None:
            initial = 0

        name = self.device_namespace.make(name=name, prefix=Capacitor.prefix)
        i = self.symbols('i_' + name)
        v, dv_dt = self.state('v_' + name, 'dv_dt_' + name, range_=range_, rel_tol=rel_tol, abs_tol=abs_tol,
                              initial=initial)

        capacitor = Capacitor(port=Port(p=p, n=n, v=v, i=i), dv_dt=dv_dt, value=value, name=name)
        self.linear_components.append(capacitor)

        return capacitor

    def transformer(self, p1, n1, p2, n2, n, name=None):
        name = self.device_namespace.make(name=name, prefix=Transformer.prefix)

        v1, i1, v2, i2 = self.symbols('v1_' + name, 'i1_' + name, 'v2_' + name, 'i2_' + name)

        transformer = Transformer(port1=Port(p=p1, n=n1, v=v1, i=i1), port2=Port(p=p2, n=n2, v=v2, i=i2), n=n, name=name)
        self.linear_components.append(transformer)

        return transformer

    def mosfet(self, p, n, ron=0.1, name=None):
        name = self.device_namespace.make(name=name, prefix=MOSFET.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        mosfet = MOSFET(port=Port(p=p, n=n, v=v, i=i), ron=ron, name=name)
        self.mosfets.append(mosfet)

        self.model.add_digital_inputs(DigitalSignal(mosfet.on))

        return mosfet

    def diode(self, p, n, vf=0, ron=0.1, name=None):
        name = self.device_namespace.make(name=name, prefix=Diode.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        diode = Diode(port=Port(p=p, n=n, v=v, i=i), vf=vf, ron=ron, name=name)
        self.diodes.append(diode)

        self.model.add_digital_states(DigitalSignal(diode.on, initial=0))

        return diode

    def solve(self, dt):
        dynamic_components = self.mosfets + self.diodes
        num_analog_cases = 2**(len(dynamic_components))
        num_digital_cases = 2**(len(self.mosfets))

        # define the digital mode variable
        digital_mode = [mosfet.on for mosfet in self.mosfets]
        digital_mode = list(reversed(digital_mode))
        digital_mode = DigitalSignal(name='d_idx', width=len(self.mosfets), expr=DigitalExpr.concat(*digital_mode))
        self.model.add_digital_modes(digital_mode)

        for diode in self.diodes:
            self.model.get_signal(diode.on).expr = DiodeExpr(num_cases=num_digital_cases, mode=digital_mode.name)

        # define analog mode variable
        analog_mode = [mosfet.on for mosfet in self.mosfets] + [diode.on for diode in self.diodes]
        analog_mode = list(reversed(analog_mode))
        analog_mode = DigitalSignal(name='a_idx', width=len(dynamic_components), expr=DigitalExpr.concat(*analog_mode))
        self.model.add_analog_modes(analog_mode)

        for analog_output in self.model.analog_outputs:
            analog_output.expr = CaseLinearExpr(num_cases=num_analog_cases, mode=analog_mode.name)

        for analog_state in self.model.analog_states:
            analog_state.expr = CaseLinearExpr(num_cases=num_analog_cases, mode=analog_mode.name)

        # enumerate all of the cases
        for i in range(num_analog_cases):
            # determine modes of dynamic components
            dynamic_modes = [bool((i >> j) & 1) for j in range(len(dynamic_components))]
            dynamic_modes = {component: ('on' if mode else 'off')
                             for component, mode in zip(dynamic_components, dynamic_modes)}

            # append the result if it exists
            logging.debug('*** Case {} ***'.format(i))
            soln = self.solve_case(dynamic_modes)
            logging.debug('solution found')

            # update analog states and outputs
            self.update_analog_states(case_no=i, soln=soln, dt=dt)
            self.update_analog_outputs(case_no=i, soln=soln)

            # update diode states if needed (i.e., all diodes off)
            if (i >> len(self.mosfets)) == 0:
                mask = (2**len(self.mosfets)) - 1
                self.update_diode_states(case_no=(i & mask), soln=soln)

    def solve_case(self, dynamic_modes):
        # create new analysis object
        analysis = NodalAnalysis()

        # handle linear components
        for component in self.linear_components:
            component.add_to_analysis(analysis)

        # handle dynamic components
        for component, mode in dynamic_modes.items():
            component.add_to_analysis(mode, analysis)

        # get the list of equations (note that the ground node equation is omitted)
        equations = [equation for node, equation in analysis.kcl.items() if node != 0]
        equations += analysis.other_equations

        # build a set of the variables to solve for
        solve_variables = set().union(*[equation.free_symbols for equation in equations])
        solve_variables -= set(symbols(input_.name) for input_ in self.model.analog_inputs)
        solve_variables -= set(symbols(state.name) for state in self.model.analog_states)

        # make sure that the system of equations is well-defined
        assert len(solve_variables) == len(equations)

        # use sympy solve to solve the system of equations
        soln = solve(equations, solve_variables)
        if not soln:
            raise Exception('No solution found.')

        return soln

    def update_diode_states(self, case_no, soln):
        # compute digital state update equations
        for diode in self.diodes:
            expr = self.model.get_signal(diode.on).expr
            expr.voltage.add_case(case_no=case_no, expr=soln[diode.port.v]-diode.vf)

    def update_analog_states(self, case_no, soln, dt):
        # apply digital state update equations
        for analog_state in self.model.analog_states:
            variable = symbols(analog_state.name)
            expr = variable + dt*soln[self.derivatives[variable]]

            analog_state.expr.add_case(case_no=case_no, expr=expr)

    def update_analog_outputs(self, case_no, soln):
        # list all output variables
        for output in self.model.analog_outputs:
            symbol = self.output_symbols[output.name]

            if symbol in soln:
                expr = soln[symbol]
            else:
                expr = symbol

            output.expr.add_case(case_no=case_no, expr=expr)