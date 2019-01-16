import subprocess
import sys

from msdsl.files import get_full_path

def call(cmd):
    ret = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stdout)

    if ret != 0:
        raise RuntimeError('Command exited with non-zero code.')

def call_python(cmd):
    # get path to python executable
    python = sys.executable
    if python is None:
        raise ValueError('Python path empty.')
    python = get_full_path(python)

    # prepend python executable to command
    cmd = [python] + cmd

    # call python
    call(cmd)

def tree_op(terms, op, default):
    if len(terms) == 0:
        return default()
    elif len(terms) == 1:
        return terms[0]
    else:
        a = tree_op(terms[:len(terms)//2], op=op, default=default)
        b = tree_op(terms[len(terms)//2:], op=op, default=default)
        return op(a, b)

def main():
    op = lambda a, b: a+b
    default = lambda: 0

    print(tree_op([], op=op, default=default))
    print(tree_op([1], op=op, default=default))
    print(tree_op([1, 2], op=op, default=default))
    print(tree_op([1, 2, 3], op=op, default=default))
    print(tree_op([1, 2, 3, 4], op=op, default=default))
    print(tree_op([1, 2, 3, 4, 5], op=op, default=default))

if __name__ == '__main__':
    main()