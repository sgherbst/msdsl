from collections import OrderedDict
from itertools import chain
from numbers import Integral
from typing import List, Set, Union
from copy import deepcopy

from msdsl.assignment import ThisCycleAssignment, NextCycleAssignment, BindingAssignment
from msdsl.expr.analyze import signal_names
from msdsl.eqn.cases import address_to_settings
from msdsl.eqn.eqn_sys import EqnSys
from msdsl.expr.expr import ModelExpr, array, concatenate, sum_op, wrap_constant, min_op
from msdsl.expr.signals import (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput, Signal, AnalogSignal,
                   AnalogState, DigitalState)
from msdsl.generator.generator import CodeGenerator
from msdsl.util import Namer
from msdsl.eqn.lds import LdsCollection
from msdsl.expr.format import RealFormat, IntFormat, is_signed

from scipy.signal import cont2discrete

class Bus:
    def __init__(self, signal: Signal, n: Integral):
        self.signal = signal
        self.n = n

class MixedSignalModel:
    def __init__(self, module_name, *ios, dt=None):
        # save settings
        self.module_name = module_name
        self.dt = dt

        # initialize
        self.signals = OrderedDict()
        self.assignments = OrderedDict()
        self.probes = []
        self.namer = Namer()

        # add ios
        for io in ios:
            self.add_signal(io)

    def __getattr__(self, item):
        return self.get_signal(item)

    def add_signal(self, x: Union[Signal, Bus]):
        if isinstance(x, Bus):
            # create the bus one signal at a time
            bus = []
            for k in range(x.n):
                signal = deepcopy(x.signal)
                signal.name = f'{signal.name}_{k}'
                bus.append(self.add_signal(signal))

            # add a property to the class with the bus name
            setattr(self, x.signal.name, bus)

            # return the bus
            return bus
        elif isinstance(x, Signal):
            # add the signal name to the namer.  this also checks that the name is not taken.
            self.namer.add_name(x.name)

            # add the signal to the model dictionary, which makes it possible to access signals as attributes of a Model
            self.signals[x.name] = x

            # return the signal.  this is a convenience that allows the user to instantiate the signal inside the call
            # to add_signal
            return x
        else:
            raise Exception(f'Unknown signal type: {x.__class__.__name__}.')

    # convenience functions for adding specific types of signals

    def add_analog_input(self, name):
        return self.add_signal(AnalogInput(name=name))

    def add_analog_output(self, name, init=0):
        return self.add_signal(AnalogOutput(name=name, init=init))

    def add_analog_state(self, name, range_, width=None, exponent=None, init=0):
        return self.add_signal(AnalogState(name=name, range_=range_, width=width, exponent=exponent, init=init))

    def add_digital_input(self, name, width=1, signed=False):
        return self.add_signal(DigitalInput(name=name, width=width, signed=signed))

    def add_digital_output(self, name, width=1, signed=False, init=0):
        return self.add_signal(DigitalOutput(name=name, width=width, signed=signed, init=init))

    def add_digital_state(self, name, width=1, signed=False, init=0):
        return self.add_signal(DigitalState(name=name, width=width, signed=signed, init=init))

    # signal access functions

    def has_signal(self, name: str):
        return name in self.signals

    def get_signal(self, name: str):
        assert self.has_signal(name), 'The signal ' + name + ' has not been defined.'
        return self.signals[name]

    def get_signals(self, names: Union[List[str], Set[str]]):
        return [self.get_signal(name) for name in names]

    def get_analog_inputs(self):
        return [signal for signal in self.signals.values() if isinstance(signal, AnalogInput)]

    def get_analog_outputs(self):
        return [signal for signal in self.signals.values() if isinstance(signal, AnalogOutput)]

    def get_digital_inputs(self):
        return [signal for signal in self.signals.values() if isinstance(signal, DigitalInput)]

    def get_digital_outputs(self):
        return [signal for signal in self.signals.values() if isinstance(signal, DigitalOutput)]

    # functions to assign signals

    def add_assignment(self, assignment):
        assert assignment.signal.name not in self.assignments, \
            'The signal ' + assignment.signal.name + ' has already been assigned.'
        self.assignments[assignment.signal.name] = assignment

    def set_this_cycle(self, signal: Signal, expr: ModelExpr):
        self.add_assignment(ThisCycleAssignment(signal=signal, expr=expr))

    def set_next_cycle(self, signal: Signal, expr: ModelExpr):
        self.add_assignment(NextCycleAssignment(signal=signal, expr=expr))

    def bind_name(self, name: str, expr: ModelExpr):
        # wrap the expression if it's a constant
        expr = wrap_constant(expr)

        # create signal to hold result
        signal = Signal(name=name, format_=expr.format_)

        # add signal to model
        self.add_signal(signal)

        # add assignment to model
        self.add_assignment(BindingAssignment(signal=signal, expr=expr))

        # return signal
        return signal

    # assignment access functions

    def has_assignment(self, name: str):
        return name in self.assignments

    def get_assignment(self, name: str):
        assert self.has_assignment(name), f'The signal {name} has not been assigned.'
        return self.assignments[name]

    def get_assignments(self, names: List[str]):
        return [self.get_assignment(name) for name in names]

    # signal probe functions

    def add_probe(self, signal: Signal):
        self.probes.append(signal)

    # signal assignment functions

    def add_counter(self, name, width, init=0, loop=False):
        self.add_digital_state(name, width=width, init=init)

        if loop:
            self.set_next_cycle(self.get_signal(name), (self.get_signal(name)+1)[(width-1):0])
        else:
            self.set_next_cycle(self.get_signal(name), min_op([self.get_signal(name) + 1, (1 << width) - 1]))

    def get_equation_io(self, eqn_sys: EqnSys):
        # determine all signals present in the set of equations
        all_signal_names = set(signal_names(eqn_sys.get_all_signals()))

        # determine inputs
        input_names = (signal_names(self.get_analog_inputs()) | self.assignments.keys()) & all_signal_names
        inputs = self.get_signals(input_names)

        # determine states
        state_names = set(signal_names(eqn_sys.get_states()))
        deriv_names = set(signal_names(eqn_sys.get_derivs()))
        states = self.get_signals(state_names)

        # determine outputs
        output_names  = (all_signal_names - input_names - state_names - deriv_names) & self.signals.keys()
        outputs = self.get_signals(output_names)

        # determine sel_bits
        sel_bit_names = set(signal_names(eqn_sys.get_sel_bits()))
        sel_bits = self.get_signals(sel_bit_names)

        # return result
        return inputs, states, outputs, sel_bits

    def add_eqn_sys(self, eqns: List[ModelExpr], extra_outputs=None):
        # set defaults
        extra_outputs = extra_outputs if extra_outputs is not None else []

        # create object to hold system of equations
        eqn_sys = EqnSys(eqns)

        # analyze equation to find out knowns and unknowns
        inputs, states, outputs, sel_bits = self.get_equation_io(eqn_sys)

        # add the extra outputs as needed
        for extra_output in extra_outputs:
            if not isinstance(extra_output, Signal):
                print('Skipping extra output ' + str(extra_output) + ' since it is not a Signal.')
            elif extra_output.name in signal_names(outputs):
                print('Skipping extra output ' + extra_output.name + \
                      ' since it is already included by default in the outputs of the system of equations.')
            else:
                outputs.append(extra_output)

        # initialize lists of matrices
        collection = LdsCollection()

        # iterate over all of the bit combinations
        for k in range(2 ** len(sel_bits)):
            # substitute values for this particular setting
            sel_bit_settings = address_to_settings(k, sel_bits)
            eqn_sys_k = eqn_sys.subst_case(sel_bit_settings)

            # convert system of equations to a linear dynamical system
            lds = eqn_sys_k.to_lds(inputs=inputs, states=states, outputs=outputs)

            # discretize linear dynamical system
            lds = lds.discretize(dt=self.dt)

            # add to collection of LDS systems
            collection.append(lds)

        # construct address for selection
        if len(sel_bits) > 0:
            sel = concatenate(sel_bits)
        else:
            sel = None

        # add the discrete-time equation
        self.add_discrete_time_lds(collection=collection, inputs=inputs, states=states, outputs=outputs, sel=sel)

    def add_discrete_time_lds(self, collection, inputs=None, states=None, outputs=None, sel=None):
        # set defaults
        inputs = inputs if inputs is not None else []
        states = states if states is not None else []
        outputs = outputs if outputs is not None else []

        # state updates.  state initialization is captured in the signal itself, so it doesn't have to be explicitly
        # captured here
        for row in range(len(states)):
            expr = sum_op([array(collection.A[row, col], sel) * states[col] for col in range(len(states))])
            expr += sum_op([array(collection.B[row, col], sel) * inputs[col] for col in range(len(inputs))])
            self.set_next_cycle(states[row], expr)

        # output updates
        for row in range(len(outputs)):
            expr = sum_op([array(collection.C[row, col], sel) * states[col] for col in range(len(states))])
            expr += sum_op([array(collection.D[row, col], sel) * inputs[col] for col in range(len(inputs))])

            # if the output signal already exists, then assign it directly.  otherwise, bind the signal name to the
            # expression value
            if self.has_signal(outputs[row].name):
                self.set_this_cycle(outputs[row], expr)
            else:
                self.bind_name(outputs[row].name, expr)

    def set_tf(self, input_, output, tf):
        # discretize transfer function
        res = cont2discrete(tf, self.dt)

        # get numerator and denominator coefficients
        b = [+float(val) for val in res[0].flatten()]
        a = [-float(val) for val in res[1].flatten()]

        # create input and output histories
        i_hist = self.make_history(input_, len(b))
        o_hist = self.make_history(output, len(a))

        # implement the filter
        expr = sum_op([coeff * var for coeff, var in chain(zip(b, i_hist), zip(a[1:], o_hist))])

        # make the assignment
        self.set_next_cycle(signal=output, expr=expr)

    def delay(self, input_: ModelExpr, time):
        # compute number of cycles for the delay
        n_cycles = int(round(time/self.dt))

        # create a history of the required length
        hist = self.make_history(first=input_, length=n_cycles+1)

        # get the last element from the history
        last = hist[n_cycles]

        # return the result
        return last

    def make_history(self, first: ModelExpr, length: Integral):
        # initialize
        hist = []

        # determine basename
        basename = first.name if hasattr(first, 'name') else next(self.namer)

        # add elements to the history one by one
        for k in range(length):
            if k == 0:
                hist.append(first)
            else:
                # create the signal
                name = f'{basename}_{k}'
                if isinstance(first.format_, RealFormat):
                    init = first.init if hasattr(first, 'init') else 0
                    curr = AnalogState(name=name, range_=first.format_.range_, width=first.format_.width,
                                       exponent=first.format_.exponent, init=init)
                elif isinstance(first.format_, IntFormat):
                    init = first.init if hasattr(first, 'init') else 0
                    curr = DigitalState(name=name, width=first.format_.width, signed=is_signed(first.format_),
                                        init=init)
                else:
                    raise Exception('Cannot determine format to use for storing history.')

                self.add_signal(curr)

                # make the update assignment
                self.set_next_cycle(signal=curr, expr=hist[k - 1])

                # add this signal to the history
                hist.append(curr)

        # return result
        return hist

    def compile(self, gen: CodeGenerator):
        # determine the I/Os and internal variables
        ios = []
        internals = []
        for signal in self.signals.values():
            if isinstance(signal, (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput)):
                ios.append(signal)
                continue
            elif not self.has_assignment(signal.name):
                raise Exception('The signal ' + signal.name + ' has not been assigned.')
            elif not isinstance(self.get_assignment(signal.name), BindingAssignment):
                internals.append(signal)

        # start module
        gen.start_module(name=self.module_name, ios=ios)

        # declare the internal variables
        if len(internals) > 0:
            gen.make_section('Declaring internal variables.')
        for signal in internals:
            gen.make_signal(signal)

        # update values of variables
        for assignment in self.assignments.values():
            # label this section of the code for debugging purposes
            gen.make_section(f'Assign signal: {assignment.signal.name}')

            # compile the expression to a signal
            result = gen.expr_to_signal(assignment.expr)

            # implement the update expression
            if isinstance(assignment, ThisCycleAssignment):
                gen.make_assign(input_=result, output=assignment.signal)
            elif isinstance(assignment, NextCycleAssignment):
                gen.make_mem(next_=result, curr=assignment.signal, init=assignment.signal.init)
            elif isinstance(assignment, BindingAssignment):
                gen.make_signal(assignment.signal)
                gen.make_assign(input_=result, output=assignment.signal)
            else:
                raise Exception('Invalid assignment type.')

        # add probe signals
        for signal in self.probes:
            gen.make_probe(signal)

        # end module
        gen.end_module()

    def compile_to_file(self, gen: CodeGenerator, filename: str):
        self.compile(gen=gen)
        gen.write_to_file(filename=filename)

    def compile_and_print(self, gen: CodeGenerator):
        self.compile(gen=gen)
        print(gen.text)

def main():
    from msdsl.eqn.deriv import Deriv
    from msdsl.eqn.cases import eqn_case
    from msdsl.expr.signals import DigitalSignal

    model = MixedSignalModel('test', AnalogInput('x'), dt=1)
    y = AnalogSignal('y')
    z = model.add_signal(AnalogSignal('z', 10))
    s = model.add_signal(DigitalSignal('s'))

    eqn_sys = EqnSys([
        y == model.x + 1,
        Deriv(z) == (y - z) * eqn_case([2, 3], [s])
    ])

    inputs, states, outputs, sel_bits = model.get_equation_io(eqn_sys)

    print('inputs:', signal_names(inputs))
    print('states:', signal_names(states))
    print('outputs:', signal_names(outputs))
    print('sel_bits:', signal_names(sel_bits))


if __name__ == '__main__':
    main()
