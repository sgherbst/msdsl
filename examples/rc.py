from msdsl.circuit import Circuit

from sympy import linear_eq_to_matrix, symbols

def main():
    # create new circuit
    cir = Circuit()

    # create variables
    input_ = cir.external('input')
    v_in, v_out = cir.internal('v_in', 'v_out')

    # instantiate linear elements
    cir.voltage_source(v_in, 0, input_, 'vol')
    cir.resistor(v_in, v_out, 1e3, 'res')
    cir.capacitor(v_out, 0, 1e-9, 'cap')

    # solve the circuit
    cir.solve()

if __name__ == '__main__':
    main()