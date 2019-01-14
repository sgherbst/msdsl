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

def adder_tree(terms, zero_func, add_func):
    if len(terms) == 0:
        return zero_func()
    elif len(terms) == 1:
        return terms[0]
    else:
        a = adder_tree(terms[:len(terms)//2], zero_func=zero_func, add_func=add_func)
        b = adder_tree(terms[len(terms)//2:], zero_func=zero_func, add_func=add_func)
        return add_func(a, b)

def main():
    zero_func = lambda: 0
    add_func = lambda a, b: a+b

    print(adder_tree([], zero_func=zero_func, add_func=add_func))
    print(adder_tree([1], zero_func=zero_func, add_func=add_func))
    print(adder_tree([1, 2], zero_func=zero_func, add_func=add_func))
    print(adder_tree([1, 2, 3], zero_func=zero_func, add_func=add_func))
    print(adder_tree([1, 2, 3, 4], zero_func=zero_func, add_func=add_func))
    print(adder_tree([1, 2, 3, 4, 5], zero_func=zero_func, add_func=add_func))

if __name__ == '__main__':
    main()