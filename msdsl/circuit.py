# warning message
print('######################################################')
print('# WARNING: The msdsl.circuit module is experimental! #')
print('######################################################')
print()

from msdsl.expr.signals import AnalogSignal
from msdsl.eqn.deriv import Deriv
from msdsl.eqn.cases import eqn_case
from msdsl.expr.extras import if_

class Circuit:
    def __init__(self, model, clk=None, rst=None):
        self.model = model
        self.clk = clk
        self.rst = rst

        self.kcl = {}
        self.eqns = []

        self.grounds = set()
        self.var_names = set()
        self.tmp_counter = 0
        self.extra_outputs = []

    def add_eqn(self, eqn):
        # add a single equation to the list of equations
        self.eqns.append(eqn)

    def add_eqns(self, *eqns):
        for eqn in eqns:
            self.add_eqn(eqn)

    def add_var_name(self, name):
        # add a single variable name to the list of registered variable names.
        # this is needed to be able to generate unique temporary variable names

        self.var_names.add(name)

    def add_var_names(self, *names):
        for name in names:
            self.add_var_name(name)

    def has_var_name(self, name):
        return name in self.var_names

    def tmp_var_name(self, prefix='tmp_circ_'):
        retval = f'{prefix}{self.tmp_counter}'

        while self.has_var_name(retval):
            self.tmp_counter += 1
            retval = f'{prefix}{self.tmp_counter}'

        self.add_var_name(retval)

        return retval

    def is_ground(self, var_name):
        return var_name in self.grounds

    def make_ground(self):
        ground = self.tmp_var_name()

        self.add_eqn(AnalogSignal(ground) == 0)
        self.grounds.add(ground)

        return ground

    def one_pin_kcl(self, net_name, curr_expr):
        # don't add to KCL equations if this is a ground node
        if net_name in self.grounds:
            return

        # initialize equation if necessary
        if net_name not in self.kcl:
            self.kcl[net_name] = 0

        # add to equation
        self.kcl[net_name] += curr_expr

    def two_pin_kcl(self, p, n, curr_expr):
        self.one_pin_kcl(p, -curr_expr)
        self.one_pin_kcl(n, +curr_expr)

    def capacitor(self, p, n, value, voltage_range):
        # add variable names if necessary
        self.add_var_names(p, n)

        # add state variable
        voltage = self.model.add_analog_state(self.tmp_var_name(), range_=voltage_range)

        # create variable for capacitor current
        current = AnalogSignal(self.tmp_var_name())

        # add related equations
        self.add_eqn(Deriv(voltage) == current / value)
        self.add_eqn(AnalogSignal(p) - AnalogSignal(n) == voltage)
        self.two_pin_kcl(p, n, current)

        return voltage

    def inductor(self, p, n, value, current_range):
        # add variable names if necessary
        self.add_var_names(p, n)

        # add state variable
        current = self.model.add_analog_state(self.tmp_var_name(), range_=current_range)

        # add related equations+
        self.add_eqn(Deriv(current) == (AnalogSignal(p) - AnalogSignal(n)) / value)
        self.two_pin_kcl(p, n, current)

        return current

    def resistor(self, p, n, value):
        # add variable names if necessary
        self.add_var_names(p, n)

        # add related equations
        self.two_pin_kcl(p, n, (AnalogSignal(p) - AnalogSignal(n)) / value)

    def current(self, p, n, value):
        # TODO: handle cases when value is (1) constant or (2) expression

        # add variable names if necessary
        self.add_var_names(p, n)

        # add related equations
        self.two_pin_kcl(p, n, value)

    def voltage(self, p, n, value):
        # TODO: handle cases when value is (1) constant or (2) expression

        # add variable names if necessary
        self.add_var_names(p, n)

        # create variable for current through voltage source
        current = AnalogSignal(self.tmp_var_name())

        # add related equations
        self.two_pin_kcl(p, n, current)
        self.add_eqn(AnalogSignal(p) - AnalogSignal(n) == value)

        # return the current through the voltage source
        return current

    def transformer(self, pri_p, pri_n, sec_p, sec_n, ratio):
        # add variable names as necessary
        self.add_var_names(pri_p, pri_n, sec_p, sec_n)

        # define current variables
        pri_curr = AnalogSignal(self.tmp_var_name())
        sec_curr = AnalogSignal(self.tmp_var_name())

        # add related equations
        self.add_eqn(AnalogSignal(sec_p)-AnalogSignal(sec_n) == ratio*(AnalogSignal(pri_p)-AnalogSignal(pri_n)))
        self.add_eqn(sec_curr == -pri_curr/ratio)
        self.two_pin_kcl(pri_p, pri_n, pri_curr)
        self.two_pin_kcl(sec_p, sec_n, sec_curr)

    def switch(self, p, n, ctl, r_on=1, r_off=1e9):
        # add variable names as necessary
        self.add_var_names(p, n)

        # add related equations
        cond = eqn_case([1/r_off, 1/r_on], [ctl])
        self.two_pin_kcl(p, n, (AnalogSignal(p) - AnalogSignal(n)) * cond)

    def diode(self, p, n, r_on=1, r_off=1e9, vf=0.9):
        # internal node
        x = self.tmp_var_name()

        # diode on/off control signal
        ctl = self.model.add_digital_state(self.tmp_var_name())

        # compute forward voltage
        vf_name = self.tmp_var_name()
        vf_signal = self.model.bind_name(vf_name, if_(ctl, vf*(1-r_on/r_off), 0))

        # model topology
        curr = self.voltage(p=p, n=x, value=vf_signal)
        self.switch(p=x, n=n, ctl=ctl, r_on=r_on, r_off=r_off)

        # set up circuit monitoring
        volt = AnalogSignal(p) - AnalogSignal(n)
        self.extra_outputs += [curr, AnalogSignal(p), AnalogSignal(n)]

        # logic to determine when the diode is on or off

        DIODE_OFF = 0
        DIODE_ON = 1

        self.model.set_next_cycle(
            ctl,
            if_(ctl == DIODE_OFF,
                if_(volt > 0,
                    DIODE_ON,
                    DIODE_OFF),
                if_(curr < 0,
                    DIODE_OFF,
                    DIODE_ON)
            )
        )

    def compile_to_eqn_list(self):
        retval = self.eqns.copy()

        for val in self.kcl.values():
            retval.append(val == 0)

        return retval