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
    op = lambda a, b: a+b
    default = lambda: 0

    print(tree_op([], op=op, default=default))
    print(tree_op([1], op=op, default=default))
    print(tree_op([1, 2], op=op, default=default))
    print(tree_op([1, 2, 3], op=op, default=default))
    print(tree_op([1, 2, 3, 4], op=op, default=default))
    print(tree_op([1, 2, 3, 4, 5], op=op, default=default))

    print(list2dict(['a', 'b', 'c']))

if __name__ == '__main__':
    main()