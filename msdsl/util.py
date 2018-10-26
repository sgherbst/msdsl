from itertools import count, combinations
from collections import Iterable
from sympy import symbols

def listify(x, type_):
    if isinstance(x, (list, tuple)):
        return x

    if isinstance(x, type_):
        return [x]

    raise ValueError('Unknown input type: {}'.format(type(x)))

# def to_interval(obj):
#     if isinstance(obj, interval):
#         return obj
#     else:
#         return interval[obj[0], obj[1]]

def all_combos(vals):
    for k in range(len(vals) + 1):
        for combo in combinations(vals, k):
            yield(set(combo))

class Namespace:
    def __init__(self):
        self.prefixes = {}
        self.names = set()

    def make(self, name=None, prefix=None, tries=None) :
        # set defaults
        if tries is None:
            tries = 100

        if name is not None:
            assert name not in self.names, 'Name already defined: ' + name
        else:
            assert prefix is not None, "Must provide prefix if name isn't provided."

            if prefix not in self.prefixes:
                self.prefixes[prefix] = count()

            for _ in range(tries):
                name = prefix + str(next(self.prefixes[prefix]))
                if name not in self.names:
                    break
            else:
                raise Exception('Could not define name with prefix: ' + prefix)


        self.names.add(name)

        return name


class SymbolNamespace(Namespace):
    def make(self, name=None, prefix=None, tries=None):
        name = super().make(name=name, prefix=prefix, tries=tries)
        return symbols(name)


class TagDict:
    def __init__(self):
        self.name_to_value = {}
        self.tag_to_name = {}

    def add(self, name, value, *tags):
        self.update({name: value}, *tags)

    def update(self, nv_dict, *tags):
        self.name_to_value.update(nv_dict)

        if tags is not None:
            for tag in tags:
                if tag not in self.tag_to_name:
                    self.tag_to_name[tag] = set()
                self.tag_to_name[tag].update(nv_dict.keys())

    def has(self, name):
        return name in self.name_to_value

    def get_by_name(self, name):
        return self.name_to_value[name]

    def get_by_tag(self, *tags):
        matching_names = self.name_to_value.keys()

        for group in tags:
            group_names = set()

            if isinstance(group, str):
                group = [group]

            for tag in group:
                if tag in self.tag_to_name:
                    group_names |= self.tag_to_name[tag]

            matching_names &= group_names

        return [self.name_to_value[name] for name in matching_names]

    def isa(self, name, *tags):
        for tag in tags:
            if tag not in self.tag_to_name or (name not in self.tag_to_name[tag]):
                return False
        return True