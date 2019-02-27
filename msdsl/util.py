from itertools import count

class Namer:
    def __init__(self, prefix: str='tmp', max_attempts=100):
        # save settings
        self.prefix = prefix
        self.max_attempts = max_attempts

        # initialize
        self.names = set()
        self.count = count()

    def _next_name(self):
        # not intended to be called directly, since the name may conflict with existing names
        return self.prefix + str(next(self.count))

    def add_name(self, name):
        assert name not in self.names, 'The request name ' + str(name) + ' has already been taken.'
        self.names.add(name)

    def tmp_name(self):
        for _ in range(self.max_attempts):
            name = self._next_name()
            if name not in self.names:
                self.add_name(name)
                return name
        else:
            raise Exception('Failed to produce a temporary name.')

def warn(s):
    print('WARNING: ' + str(s))

def tree_op(terms, op, default):
    if len(terms) == 0:
        return default()
    elif len(terms) == 1:
        return terms[0]
    else:
        a = tree_op(terms[:len(terms)//2], op=op, default=default)
        b = tree_op(terms[len(terms)//2:], op=op, default=default)
        return op(a, b)

def list2dict(l):
    return {elem: k for k, elem in enumerate(l)}

def main():
    # tree_op tests
    op = lambda a, b: a+b
    default = lambda: 0

    print(tree_op([], op=op, default=default))
    print(tree_op([1], op=op, default=default))
    print(tree_op([1, 2], op=op, default=default))
    print(tree_op([1, 2, 3], op=op, default=default))
    print(tree_op([1, 2, 3, 4], op=op, default=default))
    print(tree_op([1, 2, 3, 4, 5], op=op, default=default))

    # list2dict tests
    print(list2dict(['a', 'b', 'c']))
if __name__ == '__main__':
    main()