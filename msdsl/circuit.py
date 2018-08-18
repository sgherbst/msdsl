from sympy import symbols, solve

import logging

from msdsl.components import *
from msdsl.model import *
from msdsl.util import Namespace, all_combos

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


class StateVariable:
    def __init__(self, variable, derivative, range_):
        self.variable = variable
        self.derivative = derivative
        self.range_ = range_


class InputVariable:
    def __init__(self, variable, range_):
        self.variable = variable
        self.range_ = range_


class CircuitNamespace:
    def __init__(self):
        self.device_namespace = Namespace()
        self.symbol_namespace = Namespace()

    def make_device(self, name=None, prefix=None, tries=100):
        return self.device_namespace.make(name=name, prefix=prefix, tries=tries)

    def make_symbols(self, *args):
        retval = [symbols(self.symbol_namespace.make(arg)) for arg in args]

        if len(retval) == 1:
            return retval[0]
        else:
            return retval

class Circuit:
    def __init__(self):
        self.namespace = CircuitNamespace()

        self.input_variables = []
        self.state_variables = []
        self.internal_symbols = set()

        self.linear_components = []
        self.diodes = []
        self.mosfets = []

        self.inductors = {}

    def input_(self, name, range_=None):
        # set default
        if range_ is None:
            range_ = [-1, 1]

        variable = self.namespace.make_symbols(name)

        self.input_variables.append(InputVariable(variable=variable, range_=range_))

        return variable

    def state(self, variable_name, derivative_name, range_):
        variable, derivative = self.namespace.make_symbols(variable_name, derivative_name)

        state_variable = StateVariable(variable=variable, derivative=derivative, range_=range_)
        self.state_variables.append(state_variable)

        return state_variable

    def symbols(self, *args):
        retval = []

        for arg in args:
            symbol = self.namespace.make_symbols(arg)
            self.internal_symbols.add(symbol)

            retval.append(symbol)

        if len(retval) == 1:
            return retval[0]
        else:
            return retval

    def nodes(self, *args):
        return self.symbols(*args)

    def voltage_source(self, p, n, expr=None, name=None):
        name = self.namespace.make_device(name=name, prefix=VoltageSource.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        retval = VoltageSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.linear_components.append(retval)

        return retval

    def current_source(self, p, n, expr=None, name=None):
        name = self.namespace.make_device(name=name, prefix=CurrentSource.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        retval = CurrentSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.linear_components.append(retval)

        return retval

    def resistor(self, p, n, value, name=None):
        name = self.namespace.make_device(name=name, prefix=Resistor.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        retval = Resistor(port=Port(p=p, n=n, v=v, i=i), value=value, name=name)

        self.linear_components.append(retval)

        return retval

    def inductor(self, p, n, value, name=None, initial=0, range_=None):
        # set default
        if range_ is None:
            range_ = [-25, 25]

        name = self.namespace.make_device(name=name, prefix=Inductor.prefix)
        v = self.symbols('v_' + name)
        state_variable = self.state('i_' + name, 'di_dt_' + name, range_=range_)

        retval = Inductor(port=Port(p=p, n=n, v=v, i=state_variable.variable),
                          di_dt=state_variable.derivative, value=value, name=name, initial=initial)

        self.linear_components.append(retval)
        self.inductors[name] = retval

        return retval

    def capacitor(self, p, n, value, name=None, initial=0, range_=None):
        # set default
        if range_ is None:
            range_ = [-2e3, 2e3]

        name = self.namespace.make_device(name=name, prefix=Capacitor.prefix)
        i = self.symbols('i_' + name)
        state_variable = self.state('v_' + name, 'dv_dt_' + name, range_=range_)

        retval = Capacitor(port=Port(p=p, n=n, v=state_variable.variable, i=i),
                           dv_dt=state_variable.derivative, value=value, name=name, initial=initial)
        self.linear_components.append(retval)

        return retval

    def transformer(self, p1, n1, p2, n2, n, name=None):
        name = self.namespace.make_device(name=name, prefix=Transformer.prefix)

        v1, i1, v2, i2 = self.symbols('v1_' + name, 'i1_' + name, 'v2_' + name, 'i2_' + name)

        retval = Transformer(port1=Port(p=p1, n=n1, v=v1, i=i1), port2=Port(p=p2, n=n2, v=v2, i=i2), n=n, name=name)
        self.linear_components.append(retval)

        return retval

    def mosfet(self, p, n, name=None):
        name = self.namespace.make_device(name=name, prefix=MOSFET.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        retval = MOSFET(port=Port(p=p, n=n, v=v, i=i), name=name)
        self.mosfets.append(retval)

        return retval

    def diode(self, p, n, vf=0, name=None):
        name = self.namespace.make_device(name=name, prefix=Diode.prefix)
        v, i = self.symbols('v_' + name, 'i_' + name)

        retval = Diode(port=Port(p=p, n=n, v=v, i=i), vf=vf, name=name)
        self.diodes.append(retval)

        return retval

    def solve(self, dt, outputs=None):
        if outputs is None:
            outputs = []

        dynamic_components = self.mosfets + self.diodes
        num_cases = 2**(len(dynamic_components))

        model = MixedSignalModel()

        model.analog_inputs = [AnalogSignal(name=input_.variable.name, range_=input_.range_)
                               for input_ in self.input_variables]

        model.digital_inputs = [DigitalSignal(name=mosfet.on) for mosfet in self.mosfets]

        model.mode = [mosfet.on for mosfet in self.mosfets] + [diode.on for diode in self.diodes]
        model.mode = list(reversed(model.mode))

        model.analog_outputs = [AnalogSignal(name=output.name, expr=CaseLinearExpr(num_cases=num_cases))
                                for output in outputs]

        model.analog_states = [AnalogSignal(name=state_variable.variable.name,
                                            range_=state_variable.range_,
                                            expr=CaseLinearExpr(num_cases=num_cases))
                               for state_variable in self.state_variables]

        model.digital_states = [DigitalSignal(name=diode.on, expr=CaseLinearExpr(num_cases=num_cases))
                                for diode in self.diodes]

        for i in range(num_cases):
            # determine modes of dynamic components
            dynamic_modes = [bool((i >> j) & 1) for j in range(len(dynamic_components))]
            dynamic_modes = {component: ('on' if mode else 'off')
                             for component, mode in zip(dynamic_components, dynamic_modes)}

            # append the result if it exists
            self.solve_case(dt=dt, model=model, case_no=i, dynamic_modes=dynamic_modes)

        return model

    def solve_case(self, dt, model, case_no, dynamic_modes, max_attempts=10):
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
            solve_variables = self.internal_symbols.copy()
            solve_variables |= set(state_variable.derivative for state_variable in self.state_variables)
            solve_variables |= set(self.inductors[inductor].port.i for inductor in disabled_inductors)

            # use sympy solve to solve the system of equations
            soln = solve(equations, solve_variables)
            if not soln:
                logging.debug('no solution')
                continue

            # compute analog state update equations
            exprs = {}
            for state_variable in self.state_variables:
                if state_variable in solve_variables:
                    expr = soln[state_variable.variable]
                else:
                    expr = state_variable.variable + dt*soln[state_variable.derivative]

                exprs[state_variable.variable.name] = expr

            # apply digital state update equations
            for analog_state in model.analog_states:
                analog_state.expr.add_case(case_no=case_no, expr=exprs[analog_state.name])

            # compute digital state update equations
            exprs = {}
            for diode in self.diodes:
                if dynamic_modes[diode] == 'on':
                    expr = soln[diode.port.i]
                else:
                    expr = soln[diode.port.v] - diode.vf

                exprs[diode.on] = expr

            # apply digital state update equations
            for digital_state in model.digital_states:
                digital_state.expr.add_case(case_no=case_no, expr=exprs[digital_state.name])

            # list all output variables
            for output in model.analog_outputs:
                output.expr.add_case(case_no=case_no, expr=soln[symbols(output.name)])

            logging.debug('solution found')
            return