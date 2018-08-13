import json

def centered(text, char='*', width=50):
    x = width - len(text)

    lhs = ((x // 2) - 1)
    rhs = ((x // 2) - 1) if ((x % 2) == 0) else (x // 2)

    return (char*lhs) + ' ' + text + ' ' + (char*rhs)

def line(char='*', width=50):
    return char*width

def to_json(d, pretty=True):
    if pretty:
        # ref: https://docs.python.org/3.7/library/json.html
        kwargs = {'sort_keys': True, 'indent': 2}
    else:
        kwargs = {}

    return json.dumps(d, **kwargs)

def from_json(string):
    return json.loads(string)