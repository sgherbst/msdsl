def centered(text, char='*', width=79):
    x = width - len(text)

    lhs = ((x // 2) - 1)
    rhs = ((x // 2) - 1) if ((x % 2) == 0) else (x // 2)

    return (char*lhs) + ' ' + text + ' ' + (char*rhs)

def line(char='*', width=79):
    return char*width