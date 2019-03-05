from itertools import count

class Namer:
    def __init__(self, prefix: str='tmp', max_attempts=100):
        # save settings
        self.prefix = prefix
        self.max_attempts = max_attempts

        # initialize
        self.names = set()
        self.count = count()

    def add_name(self, name):
        assert name not in self.names, 'The request name ' + str(name) + ' has already been taken.'
        self.names.add(name)

    def _next_name(self):
        # not intended to be called directly, since the name may conflict with existing names
        return self.prefix + str(next(self.count))

    def __next__(self):
        for _ in range(self.max_attempts):
            name = self._next_name()
            if name not in self.names:
                self.add_name(name)
                return name
        else:
            raise Exception('Failed to produce a temporary name.')

def warn(s):
    print('WARNING: ' + str(s))

def list2dict(l):
    return {elem: k for k, elem in enumerate(l)}

def main():
    # list2dict tests
    print(list2dict(['a', 'b', 'c']))

if __name__ == '__main__':
    main()