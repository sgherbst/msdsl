from math import ceil, log2

def clog2(val):
    return int(ceil(log2(val)))

def get_fixed_point_exp(val, width):
    # calculate the exponent value
    if val == 0:
        # val = 0 is a special case because log2(0)=-inf
        # hence any value for the exponent will work
        exp = 0
    else:
        exp = clog2(abs(val)/((1<<(width-1))-1))

    # return the exponent
    return exp

def fixed_to_float(val, exp):
    return val*(2**exp)

def float_to_fixed(val, exp):
    return int(round(val*(2**(-exp))))