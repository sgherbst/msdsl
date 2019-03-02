def tree_op(operands, operator, default):
    if len(operands) == 0:
        return default()
    elif len(operands) == 1:
        return operands[0]
    else:
        a = tree_op(operands[:len(operands) // 2], operator=operator, default=default)
        b = tree_op(operands[len(operands) // 2:], operator=operator, default=default)
        return operator(a, b)

def main():
    # tree_op tests
    op = lambda a, b: a+b
    default = lambda: 0

    print(tree_op([], operator=op, default=default))
    print(tree_op([1], operator=op, default=default))
    print(tree_op([1, 2], operator=op, default=default))
    print(tree_op([1, 2, 3], operator=op, default=default))
    print(tree_op([1, 2, 3, 4], operator=op, default=default))
    print(tree_op([1, 2, 3, 4, 5], operator=op, default=default))

if __name__ == '__main__':
    main()