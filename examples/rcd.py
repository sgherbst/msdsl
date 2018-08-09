from msdsl.circuit import Circuit

from sympy import linear_eq_to_matrix, symbols

def main():
    # create new circuit
    cir = Circuit()

    # create variables
    input_ = cir.external('input')
    v_in, v_x, v_out = cir.internal('v_in', 'v_x', 'v_out')

    # instantiate linear elements
    cir.voltage_source(v_in, 0, input_)
    cir.resistor(v_x, v_out, 1e3)
    cir.capacitor(v_out, 0, 1e-9)

    # instantiate diode
    diode = cir.diode(v_in, v_x)

    # solve the circuit
    cir.solve(diode.port.i, diode.port.v)

if __name__ == '__main__':
    main()