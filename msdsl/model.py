from msdsl.cpp import ap_int, ap_uint, ap_fixed, ap_ufixed
from msdsl.util import TagDict, Namespace

class AnalogSignal:
    def __init__(self, name=None, range_=None, rel_tol=None, abs_tol=None, value=None, array=None, tags=None):
        # set defaults
        if (rel_tol is None) and (abs_tol is None):
            rel_tol = 5e-7
        if tags is None:
            tags = []

        # save settings
        self.name = name
        self.range_ = range_
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol
        self.value = value
        self.array = array
        self.tags = tags

    def to_hls(self):
        # TODO: allow fixed point
        return 'float'

    def isa(self, tag):
        return tag in self.tags


class AnalogInput(AnalogSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['analog', 'input'], **kwargs)


class AnalogOutput(AnalogSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['analog', 'output'], **kwargs)


class AnalogState(AnalogSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['analog', 'state'], **kwargs)


class AnalogInternal(AnalogSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['analog', 'internal'], **kwargs)


class AnalogConstant(AnalogSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['analog', 'constant'], **kwargs)


class DigitalSignal:
    def __init__(self, name=None, signed=None, width=None, value=None, array=None, tags=None):
        # set defaults
        if signed is None:
            signed = False
        if width is None:
            width = 1
        if tags is None:
            tags = []

        self.name = name
        self.signed = signed
        self.width = width
        self.value = value
        self.array = array
        self.tags = tags

    def to_hls(self):
        if self.signed:
            return ap_int(self.width)
        else:
            return ap_uint(self.width)

    def isa(self, tag):
        return tag in self.tags


class DigitalInput(DigitalSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['digital', 'input'], **kwargs)


class DigitalOutput(DigitalSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['digital', 'output'], **kwargs)


class DigitalState(DigitalSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['digital', 'state'], **kwargs)


class DigitalInternal(DigitalSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['digital', 'internal'], **kwargs)


class DigitalConstant(DigitalSignal):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, tags=['digital', 'constant'], **kwargs)


class AssignmentGroup:
    def __init__(self, group=None):
        if group is None:
            group = []
        self.group = group


class ModelAssignment:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs


class MixedSignalModel:
    def __init__(self, analog_signals=None, digital_signals=None, assignment_groups=None):
        # initialize model
        self.tag_dict = TagDict()
        self.assignment_groups = []
        self.namespace = Namespace()

        # apply inputs when relevant
        if analog_signals is not None:
            for analog_signal in analog_signals:
                self.add(analog_signal)

        if digital_signals is not None:
            for digital_signal in digital_signals:
                self.add(digital_signal)

        if assignment_groups is not None:
            for assignment_group in assignment_groups:
                self.assign(*[(assignment.lhs, assignment.rhs) for assignment in assignment_group])

    # get specific I/O by tags

    @property
    def analog_signals(self):
        return self.tag_dict.get_by_tag('analog')

    @property
    def digital_signals(self):
        return self.tag_dict.get_by_tag('digital')

    @property
    def analog_inputs(self):
        return self.tag_dict.get_by_tag('analog', 'input')

    @property
    def analog_outputs(self):
        return self.tag_dict.get_by_tag('analog', 'output')

    @property
    def analog_states(self):
        return self.tag_dict.get_by_tag('analog', 'state')

    @property
    def analog_constants(self):
        return self.tag_dict.get_by_tag('analog', 'constant')

    @property
    def ios(self):
        return self.tag_dict.get_by_tag(('input', 'output'))

    @property
    def constants(self):
        return self.tag_dict.get_by_tag('constant')

    @property
    def states(self):
        return self.tag_dict.get_by_tag('state')

    # get specific I/O by name

    def has(self, name):
        return self.tag_dict.has(name)

    def get_by_name(self, name):
        return self.tag_dict.get_by_name(name)

    def get_by_tag(self, name, *tags):
        return self.tag_dict.get_by_tag(name, *tags)

    def isa(self, name, *tags):
        return self.tag_dict.isa(name, *tags)

    # model building

    def add(self, signal):
        self.tag_dict.add(signal.name, signal, *signal.tags)

    def assign(self, *assignments):
        assignment_group = [ModelAssignment(lhs=lhs, rhs=rhs) for lhs, rhs in assignments]
        self.assignment_groups.append(assignment_group)