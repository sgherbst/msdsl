class Port:
    def __init__(self, p, n, v, i):
        self.p = p
        self.n = n
        self.v = v
        self.i = i

    def add_to_analysis(self, analysis):
        analysis.set_equal(self.v, self.p - self.n)
        analysis.add_current(self.p, self.n, self.i)


class VoltageSource:
    prefix = 'V'

    def __init__(self, port, expr, name):
        self.port = port
        self.expr = expr
        self.name = name

    def add_to_analysis(self, analysis):
        self.port.add_to_analysis(analysis)

        analysis.set_equal(self.port.v, self.expr)


class CurrentSource:
    prefix = 'I'

    def __init__(self, port, expr, name):
        self.port = port
        self.expr = expr
        self.name = name

    def add_to_analysis(self, analysis):
        self.port.add_to_analysis(analysis)

        analysis.set_equal(self.port.i, self.expr)


class Resistor:
    prefix = 'R'

    def __init__(self, port, value, name):
        self.port = port
        self.value = value
        self.name = name

    def add_to_analysis(self, analysis):
        self.port.add_to_analysis(analysis)

        analysis.set_equal(self.port.i, self.port.v/self.value)


class Inductor:
    prefix = 'L'

    def __init__(self, port, di_dt, value, name):
        self.port = port
        self.di_dt = di_dt
        self.value = value
        self.name = name

    def add_to_analysis(self, analysis):
        self.port.add_to_analysis(analysis)

        analysis.set_equal(self.di_dt, self.port.v/self.value)


class Capacitor:
    prefix = 'C'

    def __init__(self, port, dv_dt, value, name):
        self.port = port
        self.dv_dt = dv_dt
        self.value = value
        self.name = name

    def add_to_analysis(self, analysis):
        self.port.add_to_analysis(analysis)

        analysis.set_equal(self.dv_dt, self.port.i/self.value)


class Transformer:
    prefix = 'T'

    def __init__(self, port1, port2, n, name):
        self.port1 = port1
        self.port2 = port2
        self.n = n
        self.name = name

    def add_to_analysis(self, analysis):
        self.port1.add_to_analysis(analysis)
        self.port2.add_to_analysis(analysis)

        analysis.set_equal(self.n*self.port1.v, self.port2.v)
        analysis.set_equal(-self.port1.i/self.n, self.port2.i)


class MOSFET:
    prefix = 'M'

    def __init__(self, port, name):
        self.port = port
        self.name = name

    def add_to_analysis(self, state, analysis):
        self.port.add_to_analysis(analysis)

        if state == 'on':
            analysis.set_equal(self.port.v, 0)
        else:
            analysis.set_equal(self.port.i, 0)

    @property
    def on(self):
        return self.name + '_on'

class Diode:
    prefix = 'D'

    def __init__(self, port, vf, name):
        self.port = port
        self.vf = vf
        self.name = name

    def add_to_analysis(self, state, analysis):
        self.port.add_to_analysis(analysis)

        if state == 'on':
            analysis.set_equal(self.port.v, self.vf)
        else:
            analysis.set_equal(self.port.i, 0)

    @property
    def on(self):
        return self.name + '_on'