from sympy import solve, symbols
import logging

from msdsl.components import *
from msdsl.model import *
from msdsl.util import Namespace, SymbolNamespace, all_combos


class NodalAnalysis:
    def __init__(self):
        self.kcl = {}
        self.other_equations = []

    @property
    def equations(self):
        return list(self.kcl.values()) + self.other_equations

    def set_equal(self, lhs, rhs):
        self.other_equations.append(lhs - rhs)

    def add_current(self, p, n, expr):
        self.kcl[p] = self.kcl.get(p, 0) - expr
        self.kcl[n] = self.kcl.get(n, 0) + expr


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

    def input_(self, name, range_=None, rel_tol=None, abs_tol=None):
        if range_ is None:
            range_ = [-10, 10]

        self.model.add_analog_inputs(AnalogSignal(name=name, range_=range_, rel_tol=rel_tol, abs_tol=abs_tol))

        return self.symbol_namespace.make(name)

    def output(self, sym, rel_tol=None, abs_tol=None):
        self.model.add_analog_outputs(AnalogSignal(name=sym.name, rel_tol=rel_tol, abs_tol=abs_tol))

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

    def mosfet(self, p, n, name=None):
        name = self.device_namespace.make(name=name, prefix=MOSFET.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        mosfet = MOSFET(port=Port(p=p, n=n, v=v, i=i), name=name)
        self.mosfets.append(mosfet)

        self.model.add_digital_inputs(DigitalSignal(mosfet.on))

        return mosfet

    def diode(self, p, n, vf=0, name=None):
        name = self.device_namespace.make(name=name, prefix=Diode.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        diode = Diode(port=Port(p=p, n=n, v=v, i=i), vf=vf, name=name)
        self.diodes.append(diode)

        self.model.add_digital_states(DigitalSignal(diode.on))

        return diode

    def solve(self, dt):
        dynamic_components = self.mosfets + self.diodes
        num_cases = 2**(len(dynamic_components))

        self.model.mode = [mosfet.on for mosfet in self.mosfets] + [diode.on for diode in self.diodes]
        self.model.mode = list(reversed(self.model.mode))

        for analog_output in self.model.analog_outputs:
            analog_output.expr = CaseLinearExpr(num_cases=num_cases)

        for analog_state in self.model.analog_states:
            analog_state.expr = CaseLinearExpr(num_cases=num_cases)

        for digital_state in self.model.digital_states:
            digital_state.expr = CaseLinearExpr(num_cases=num_cases)

        for i in range(num_cases):
            # determine modes of dynamic components
            dynamic_modes = [bool((i >> j) & 1) for j in range(len(dynamic_components))]
            dynamic_modes = {component: ('on' if mode else 'off')
                             for component, mode in zip(dynamic_components, dynamic_modes)}

            # append the result if it exists
            self.solve_case(dt=dt, case_no=i, dynamic_modes=dynamic_modes)

    def solve_case(self, dt, case_no, dynamic_modes, max_attempts=10):
        # create new analysis object
        analysis = NodalAnalysis()

        # handle linear components
        for component in self.linear_components:
            component.add_to_analysis(analysis)

        # handle dynamic components
        for component, mode in dynamic_modes.items():
            component.add_to_analysis(mode, analysis)

        # loop through the configs until a solution is found
        logging.debug('*** Case {} ***'.format(case_no))

        for attempt, disabled_inductors in enumerate(all_combos(self.inductors.keys())):

            if attempt >= max_attempts:
                return

            logging.debug('attempt {}'.format(attempt))

            # build a list of the equations to solve
            equations = analysis.equations.copy()
            equations.extend(self.inductors[inductor].di_dt for inductor in disabled_inductors)

            # build a set of the variables to solve for
            solve_variables = set().union(*[equation.free_symbols for equation in equations])
            solve_variables -= set(symbols(input_.name) for input_ in self.model.analog_inputs)
            solve_variables -= set(symbols(state.name) for state in self.model.analog_states)
            solve_variables |= set(self.inductors[inductor].port.i for inductor in disabled_inductors)

            # use sympy solve to solve the system of equations
            soln = solve(equations, solve_variables)
            if not soln:
                logging.debug('no solution')
                continue

            # apply digital state update equations
            for analog_state in self.model.analog_states:
                variable = symbols(analog_state.name)

                if variable in solve_variables:
                    expr = soln[variable]
                else:
                    expr = variable + dt*soln[self.derivatives[variable]]

                analog_state.expr.add_case(case_no=case_no, expr=expr)

            # compute digital state update equations
            for diode in self.diodes:
                if dynamic_modes[diode] == 'on':
                    expr = soln[diode.port.i]
                else:
                    expr = soln[diode.port.v] - diode.vf

                self.model.get_signal(diode.on).expr.add_case(case_no=case_no, expr=expr)

            # list all output variables
            for output in self.model.analog_outputs:
                output.expr.add_case(case_no=case_no, expr=soln[symbols(output.name)])

            logging.debug('solution found')
            return