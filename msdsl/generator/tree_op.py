def tree_op(operands, operator):
    if len(operands) == 1:
        return operands[0]
    elif len(operands) > 1:
        a = tree_op(operands[:len(operands) // 2], operator=operator)
        b = tree_op(operands[len(operands) // 2:], operator=operator)
        return operator(a, b)
    else:
        raise Exception('Tree operation cannot be applied to an empty list.')

def main():
    # tree_op tests
    op = lambda a, b: a+b

    print(tree_op([1], operator=op))
    print(tree_op([1, 2], operator=op))
    print(tree_op([1, 2, 3], operator=op))
    print(tree_op([1, 2, 3, 4], operator=op))
    print(tree_op([1, 2, 3, 4, 5], operator=op))

if __name__ == '__main__':
    main()