from sympy import symbols, solve, linsolve, S
from itertools import count, combinations

from msdsl.components import *
from msdsl.util import *

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
    def __init__(self, variable, derivative):
        self.variable = variable
        self.derivative = derivative


class ComponentNamer:
    def __init__(self):
        self.prefixes = {}

    def make(self, prefix):
        if prefix not in self.prefixes:
            self.prefixes[prefix] = count()

        return prefix + str(next(self.prefixes[prefix]))


class SymbolNamespace:
    def __init__(self):
        self.sym_names = set()

    def define(self, *args):
        # check that variable names are unique
        for arg in args:
            assert arg not in self.sym_names, 'Variable already defined: ' + arg
            self.sym_names.add(arg)

        # return new symbol(s)
        return symbols(args)


class Circuit:
    def __init__(self):
        self.namespace = SymbolNamespace()
        self.namer = ComponentNamer()

        self.ext_syms = []
        self.int_syms = []

        self.state_vars = []

        self.static_comps = []
        self.dynamic_comps = []

        self.inductor_state_vars = []

    def external(self, *args):
        retval = self.namespace.define(*args)

        self.ext_syms.extend(retval)

        if len(args) == 1:
            return retval[0]
        else:
            return retval

    def internal(self, *args):
        retval = self.namespace.define(*args)

        self.int_syms.extend(retval)

        if len(args) == 1:
            return retval[0]
        else:
            return retval

    def state(self, variable, derivative):
        retval = StateVariable(variable=variable, derivative=derivative)

        self.state_vars.append(retval)

        return retval

    def voltage_source(self, p, n, expr=None, name=None):
        name = name if name is not None else self.namer.make(VoltageSource.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = VoltageSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.static_comps.append(retval)

        return retval

    def current_source(self, p, n, expr=None, name=None):
        name = name if name is not None else self.namer.make(CurrentSource.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = CurrentSource(port=Port(p=p, n=n, v=v, i=i), expr=expr, name=name)

        self.static_comps.append(retval)

        return retval

    def resistor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Resistor.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = Resistor(port=Port(p=p, n=n, v=v, i=i), value=value, name=name)

        self.static_comps.append(retval)

        return retval

    def inductor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Inductor.prefix)
        v, i, di_dt = self.internal('v_' + name, 'i_' + name, 'di_dt_' + name)

        state = self.state(variable=i, derivative=di_dt)
        self.inductor_state_vars.append(state)

        retval = Inductor(port=Port(p=p, n=n, v=v, i=i), state=state, value=value, name=name)

        self.static_comps.append(retval)

        return retval

    def capacitor(self, p, n, value, name=None):
        name = name if name is not None else self.namer.make(Capacitor.prefix)
        v, i, dv_dt = self.internal('v_' + name, 'i_' + name, 'dv_dt_' + name)

        state = self.state(variable=v, derivative=dv_dt)

        retval = Capacitor(port=Port(p=p, n=n, v=v, i=i), state=state, value=value, name=name)
        self.static_comps.append(retval)

        return retval

    def transformer(self, p1, n1, p2, n2, n, name=None):
        name = name if name is not None else self.namer.make(Transformer.prefix)
        v1, i1, v2, i2 = self.internal('v1_' + name, 'i1_' + name, 'v2_' + name, 'i2_' + name)

        retval = Transformer(port1=Port(p=p1, n=n1, v=v1, i=i1), port2=Port(p=p2, n=n2, v=v2, i=i2), n=n, name=name)
        self.static_comps.append(retval)

        return retval

    def mosfet(self, p, n, name=None):
        name = name if name is not None else self.namer.make(MOSFET.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = MOSFET(port=Port(p=p, n=n, v=v, i=i), name=name)
        self.dynamic_comps.append(retval)

        return retval

    def diode(self, p, n, vf=0, name=None):
        name = name if name is not None else self.namer.make(Diode.prefix)
        v, i = self.internal('v_' + name, 'i_' + name)

        retval = Diode(port=Port(p=p, n=n, v=v, i=i), vf=vf, name=name)
        self.dynamic_comps.append(retval)

        return retval

    def solve(self, *observe_vars):
        first = True
        for i in range(2**len(self.dynamic_comps)):
            if first:
                first = False
            else:
                print()

            comp_states = [bool((i >> j) & 1) for j in range(len(self.dynamic_comps))]

            print(centered('Case ' + str(i+1)))
            self.solve_single(observe_vars=observe_vars, comp_states=comp_states)
            print(line())

    def solve_single(self, observe_vars=None, comp_states=None, max_attempts=10):
        # set defaults

        if observe_vars is None:
            observe_vars = []
        if comp_states is None:
            comp_states = []

        # print out the state of the dynamic components

        dynamic_states = [comp.name + ': ' + ('on' if state else 'off')
                          for comp, state in zip(self.dynamic_comps, comp_states)]

        print('Switch States')
        if dynamic_states:
            print('\n'.join(dynamic_states))
        else:
            print('N/A')
        print()

        # create new analysis object

        analysis = NodalAnalysis()

        # handle static components

        for comp in self.static_comps:
            comp.add_to_analysis(analysis)

        # handle dynamic components

        for comp, state in zip(self.dynamic_comps, comp_states):
            comp.add_to_analysis(state, analysis)

        # generate a list of different configurations to try, in which different combinations of
        # inductors are effectively disabled

        configs = []
        for k in range(len(self.inductor_state_vars)+1):
            done = False
            for combo in combinations(self.inductor_state_vars, k):
                if len(configs) < max_attempts:
                    configs.append(set(combo))
                else:
                    done = True
                    break
            if done:
                break

        # loop through the configs until a solution is found

        for disabled_state_vars in configs:

            solve_vars = self.int_syms[:]
            eqns = analysis.equations[:]

            for state_var in self.state_vars:
                if state_var not in disabled_state_vars:
                    solve_vars.remove(state_var.variable)
                else:
                    eqns.append(state_var.derivative)

            # solve the modified system of equations

            # sympy linsolve approach (seems to be buggy)
            # soln = linsolve(eqns, solve_vars)
            # if len(soln) != 1:
            #     continue
            # soln = dict(zip(solve_vars, next(iter(soln))))

            # sympy solve approach
            soln = solve(eqns, solve_vars)
            if not soln:
                continue

            print('State Variables')
            for state_var in self.state_vars:
                if state_var not in disabled_state_vars:
                    print(state_var.derivative.name + ': ' + str(soln[state_var.derivative]))
                else:
                    print(state_var.variable.name + ': ' + str(soln[state_var.variable]))
            if not self.state_vars:
                print('N/A')
            print()

            print('Output Variables')
            for v in observe_vars:
                print(v.name + ': ' + str(soln[v]))
            if not observe_vars:
                print('N/A')

            break
        else:
            print('No solutions found.')