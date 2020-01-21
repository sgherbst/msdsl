from collections import OrderedDict
from itertools import chain
from numbers import Integral, Number
from typing import List, Set, Union
from copy import deepcopy

from math import ceil, log2

from msdsl.assignment import ThisCycleAssignment, NextCycleAssignment, BindingAssignment, Assignment
from msdsl.expr.analyze import signal_names
from msdsl.eqn.cases import address_to_settings
from msdsl.eqn.eqn_sys import EqnSys
from msdsl.expr.expr import ModelExpr, array, concatenate, sum_op, wrap_constant, min_op
from msdsl.expr.signals import (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput, Signal, AnalogSignal,
                   AnalogState, DigitalState, RealParameter, DigitalSignal)
from msdsl.generator.generator import CodeGenerator
from msdsl.util import Namer
from msdsl.eqn.lds import LdsCollection
from msdsl.expr.format import RealFormat, IntFormat, is_signed
from msdsl.expr.extras import if_
from msdsl.circuit import Circuit

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
        self.circuits = []
        self.real_params = []
        self.namer = Namer()

        # add ios
        for io in ios:
            self.add_signal(io)

    def __getattr__(self, item):
        return self.get_signal(item)

    def add_signal(self, x: Union[Signal, Bus]):
        """
        Adds a signal or bus object to the model, meaning that it can be accessed by name later.  For example, if
        we run m.add_signal(Signal(name="abc")), we can access the signal afterwards using m.abc

        :param x: Signal or Bus object to be added
        :return: The signal object
        """

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
        """
        Note that the initial value will only be used if the analog output has state.
        """
        return self.add_signal(AnalogOutput(name=name, init=init))

    def add_analog_state(self, name, range_, width=None, exponent=None, init=0):
        """
        Note that analog states used in a system of equations must be adding using this method or the more generic
        add_signal method before calling add_eqn_sys.

        :param range_:  The +/- range of the analog value.  For example, if range_=1.23, then the state variable will
                        fall between +/-1.23.  Note that range is *required* for an analog state, since we don't have any
                        other way to determine the range of the signal for fixed-point formatting purposes.

        :param init:    The initial value of the analog signal.  This is the reset value of the state variable when
                        `RST_MSDSL is asserted (synchronous reset).
        """
        return self.add_signal(AnalogState(name=name, range_=range_, width=width, exponent=exponent, init=init))

    def add_digital_signal(self, name, width=1, signed=False):
        """
        Allows for a digital signal to be declared ahead of time with a given format.  In general, it is preferable
        to use bind_name for this, rather than calling add_digital_signal followed by set_this_cycle.
        """
        return self.add_signal(DigitalSignal(name=name, width=width, signed=signed))

    def add_digital_input(self, name, width=1, signed=False):
        return self.add_signal(DigitalInput(name=name, width=width, signed=signed))

    def add_digital_output(self, name, width=1, signed=False, init=0):
        """
        Note that the initial value will only be used if the digital output has state.
        """
        return self.add_signal(DigitalOutput(name=name, width=width, signed=signed, init=init))

    def add_digital_state(self, name, width=1, signed=False, init=0):
        """

        :param init:    The initial value of the digital signal.  This is the reset value of the state variable when
                        `RST_MSDSL is asserted (synchronous reset).
        """
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

    def add_assignment(self, assignment: Assignment):
        assert assignment.signal.name not in self.assignments, \
            'The signal ' + assignment.signal.name + ' has already been assigned.'

        self.assignments[assignment.signal.name] = assignment

        return assignment.signal

    def immediate_assign(self, signal: Union[Signal, str], expr: ModelExpr):
        """
        Alias for set_this_cycle.
        """

        return self.set_this_cycle(signal=signal, expr=expr)

    def bind_name(self, signal: Union[Signal, str], expr: ModelExpr):
        """
        TODO: consider deprecating.
        Alias for set_this_cycle.
        """

        return self.set_this_cycle(signal=signal, expr=expr)

    def set_this_cycle(self, signal: Union[Signal, str], expr: ModelExpr):
        """
        The behavior of this function is essentially a blocking assignment (in Verilog nomenclature). The provided
        expression is continuously written to the provided signal.

        :param signal:  Signal object being assigned
        :param expr:    Value of the expression to assign
        :return:
        """

        if isinstance(signal, str):
            expr = wrap_constant(expr)
            signal = self.add_signal(Signal(name=signal, format_=expr.format_))
            assignment_cls = BindingAssignment
        elif isinstance(signal, Signal):
            assignment_cls = ThisCycleAssignment
        else:
            raise Exception(f'Invalid signal type: {type(signal)}.')

        return self.add_assignment(assignment_cls(signal=signal, expr=expr))

    def next_cycle_assign(self, signal: Signal, expr: ModelExpr, clk=None, rst=None, ce=None):
        """
        Alias for set_next_cycle.
        """

        return self.set_next_cycle(signal=signal, expr=expr, clk=clk, rst=rst, ce=ce)

    def set_next_cycle(self, signal: Signal, expr: ModelExpr, clk=None, rst=None, ce=None):
        """
        The behavior of this function is essentially a non-blocking assignment (in Verilog nomenclature). The provided
        expression is written to the provided signal at the next positive edge of the clock signal.

        :param signal:  Signal object being assigned
        :param expr:    Value of the expression to assign
        :param clk:     Optional input.  Will use `CLK_MSDSL by default.
        :param rst:     Optional input for synchronous reset.  Will use `RST_MSDSL by default.
        :param ce:      Optional input for clock enable.  Will use "1" (i.e., always enabled) by default.
        :return:
        """

        return self.add_assignment(NextCycleAssignment(signal=signal, expr=expr, clk=clk, rst=rst, ce=ce))

    # assignment access functions

    def has_assignment(self, name: str):
        return name in self.assignments

    def get_assignment(self, name: str):
        assert self.has_assignment(name), f'The signal {name} has not been assigned.'
        return self.assignments[name]

    def get_assignments(self, names: List[str]):
        return [self.get_assignment(name) for name in names]

    # parameter functions

    def add_real_param(self, name: str, default: Number):
        """
        Equivalent to a real parameter in a Verilog module definition.  Allows the user to generate a single
        SystemVerilog model that can be used for various purposes.

        :param name:        Name of the parameter.
        :param default:     Real number default for the parameter.  A ModelExpr is not allowed here.
        :return:            Returns a signal representing the parameter that can be used in subsequent expressions.
        """

        param = RealParameter(param_name=f'{name}', signal_name=f'{name}_param', default=default)
        self.real_params.append(param)

        setattr(self, name, param)

        return param

    # signal probe functions

    def add_probe(self, signal: Signal):
        """
        Designate a signal for probing via the ILA.  Works with both analog and digital signals.
        """
        self.probes.append(signal)

    # signal assignment functions

    def add_counter(self, name, width, init=0, loop=False, clk=None, rst=None, ce=None):
        """
        Instantiates a counter with a user-specified connections.  Intended for stimulus generation via lookup table.

        :param name:    Name of the digital signal used to hold the counter value.
        :param width:   Width of digital signal, which affects the counter range.
        :param init:    Optional initial value for the counter.
        :param loop:    If True, allow the counter to overflow.  Otherwise freeze the counter at the maximum value.
        :param clk:     Optional clock input.  Defaults to `CLK_MSDSL.
        :param rst:     Optional synchronous reset input.  Defaults to `RST_MSDSL.
        :param ce:      Option clock enable input.  Defaults to "1".
        :return:
        """

        self.add_digital_state(name, width=width, init=init)

        if loop:
            self.set_next_cycle(self.get_signal(name), (self.get_signal(name)+1)[(width-1):0],
                                clk=clk, rst=rst, ce=ce)
        else:
            self.set_next_cycle(self.get_signal(name), min_op([self.get_signal(name)+1, (1<<width)-1]),
                                clk=clk, rst=rst, ce=ce)

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

    def add_eqn_sys(self, eqns: List[ModelExpr], extra_outputs=None, clk=None, rst=None):
        """
        Accepts a list of equations that can contain derivatives of analog state variables.  The approach used is
        to convert the system of differential equations into a standard-form linear dynamical system (reference:
        http://ee263.stanford.edu/lectures/linsys.pdf).  If there are several eqn_cases to be considered, we construct
        a different LDS for each one.  These LDS's are discretized using the given timestep by using the exponential
        matrix function assuming piecewise-constant input (sometimes known as the zero-order hold approach).

        :param eqns:            List of equations.
        :param extra_outputs:   List of internal variables in the system of equations that should be bound to analog signals.
        :param clk:             Name of clock signal to use (None will default to `CLK_MSDSL)
        :param rst:             Name of the reset signal to use (None will default to `RST_MSDSL)
        """

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
        self.add_discrete_time_lds(collection=collection, inputs=inputs,
                                   states=states, outputs=outputs, sel=sel,
                                   clk=clk, rst=rst)

    def add_discrete_time_lds(self, collection, inputs=None, states=None, outputs=None, sel=None,
                              clk=None, rst=None):
        # set defaults
        inputs = inputs if inputs is not None else []
        states = states if states is not None else []
        outputs = outputs if outputs is not None else []

        # state updates.  state initialization is captured in the signal itself, so it doesn't have to be explicitly
        # captured here
        for row in range(len(states)):
            expr = sum_op([array(collection.A[row, col], sel) * states[col] for col in range(len(states))])
            expr += sum_op([array(collection.B[row, col], sel) * inputs[col] for col in range(len(inputs))])
            self.set_next_cycle(states[row], expr, clk=clk, rst=rst)

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

    def set_tf(self, input_: Signal, output: Signal, tf):
        """
        Method to assign an output signal as a function of the input signal by applying a given transfer function.
        The transfer function is discretized using a timestep of "dt" by applying the zero-order hold method.

        :param input_:      Input signal.
        :param output:      Output signal (should be an AnalogState that is not yet assigned)
        :param tf:          Tuple consisting of a list of numerator coefficients and a list of denominator coefficients.  See
                            https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.cont2discrete.html for more details.
        :return:
        """

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

    def inertial_delay(self, input_: ModelExpr, tr: Number, tf: Number):
        """
        Applies a resource-efficient implementation of a long delay for *one-bit digital signals only*.  Note that the
        pulse width of the input expression should be wider than the delay, otherwise the signal will be filtered.

        :param input_:  Expression that should be delayed.  Must evaluate to a one-bit signal.
        :param tr:      Rising edge delay, in seconds.
        :param tf:      Falling edge delay, in seconds.
        :return:        Object representing the delayed signal, which should be assigned to another signal using
                        immediate_assign.
        """

        # input type checking
        assert isinstance(input_.format_, IntFormat) and input_.format_.width == 1, \
            'Inertial delay only supports one-bit signals at this time.'

        # determine number of cycles to delay
        tr_int = int(round(tr/self.dt))
        tf_int = int(round(tf/self.dt))

        # determine counter width
        width = int(ceil(log2(1+max(tr_int, tf_int))))

        # determine base name
        basename = input_.name if hasattr(input_, 'name') else next(self.namer)

        # create output and counter variable
        in_ = self.bind_name(basename+'_in', input_)
        count = self.add_digital_state(name=basename+'_count', width=width, signed=False)
        out = self.add_digital_state(name=basename+'_out', width=1, signed=False)
        target = if_(in_, tr_int, tf_int)
        done = self.bind_name(basename+'_done', (out == in_) | (count == target))

        self.set_next_cycle(out,   if_(done, in_, out))
        self.set_next_cycle(count, if_(done, 0, (count+1)[(width-1):0]))

        return out

    def delay(self, input_: ModelExpr, time, max_cycles=100):
        """
        Delays an analog or digital signal by the specified time.  Note that this does *not* currently use a
        resource-efficient implementation.

        :param input_:      Expression that should be delayed.
        :param time:        Delay time in seconds.
        :param max_cycles:  Maximum number of delay cycles allowed.
        :return:            Object representing the delayed signal, which should be assigned to another signal using
                            immediate_assign.
        """

        # compute number of cycles for the delay
        n_cycles = int(round(time/self.dt))
        assert n_cycles <= max_cycles, \
            f'The length of the register chain for this delay will be {n_cycles} emulator cycles, which is greater than the user-provided maximum of {max_cycles}.  '+\
            f'Please update the max_cycles function argument to clear this assertion error.'

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

    def make_circuit(self):
        c = Circuit(self)
        self.circuits.append(c)
        return c

    def compile(self, gen: CodeGenerator):
        # compile circuits
        for circuit in self.circuits:
            eqns = circuit.compile_to_eqn_list()
            self.add_eqn_sys(eqns, circuit.extra_outputs)

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
        gen.start_module(name=self.module_name, ios=ios, real_params=self.real_params)

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
                gen.make_mem(next_=result, curr=assignment.signal, init=assignment.signal.init, clk=assignment.clk,
                             rst=assignment.rst, ce=assignment.ce)
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
        """
        Compiles the model using the provided CodeGenerator, and writes the resulting model to the given filename.
        """
        self.compile(gen=gen)
        gen.write_to_file(filename=filename)

    def compile_and_print(self, gen: CodeGenerator):
        """
        Compiles the model using the provided CodeGenerator, and then prints the resulting model to the console.
        This is mainly used for demonstration and debug purposes.
        """
        self.compile(gen=gen)
        print(gen.text)

    # probe functions

    def _probe_selective(self, filter_func=None, io_only=True):
        # start with all signals
        probe_list = self.signals.values()

        # limit selection to just IOs if desired
        if io_only:
            io_types = (AnalogInput, AnalogOutput, DigitalInput, DigitalOutput)
            probe_list = [signal for signal in probe_list if isinstance(signal, io_types)]

        # apply further filtering if desired
        if filter_func is not None:
            probe_list = [signal for signal in probe_list if filter_func(signal)]

        # attach probes to remaining signals
        for signal in probe_list:
            self.add_probe(signal)

    def probe_all(self, io_only=True):
        """
        Attach probes to all signals (analog or digital).  By default this only applies to signals that appear in the
        module I/O list.  Set io_only to False to probe everything.
        """
        self._probe_selective(io_only=io_only)

    def probe_analog(self, io_only=True):
        """
        Attach probes to analog signals.  By default this only applies to analog signals that appear in the module I/O
        list.  Set io_only to False to probe all analog signals.
        """
        filter_func = lambda signal: isinstance(signal.format_, RealFormat)
        self._probe_selective(filter_func=filter_func, io_only=io_only)

    def probe_digital(self, io_only=True):
        """
        Attach probes to digital signals.  By default this only applies to analog signals that appear in the module I/O
        list.  Set io_only to False to probe all analog signals.
        """
        filter_func = lambda signal: isinstance(signal.format_, IntFormat)
        self._probe_selective(filter_func=filter_func, io_only=io_only)

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