`include "svreal.sv"

module test_circuit_sw (
    input real v_in,
    output real v_out,
    input sw1,
    input sw2
);
    `MAKE_REAL(v_in_int, 5);
    assign `FORCE_REAL(v_in, v_in_int);

    `MAKE_REAL(v_out_int, 5);
    assign v_out = `TO_REAL(v_out_int);

    model #(
        `PASS_REAL(v_in, v_in_int),
        `PASS_REAL(v_out, v_out_int)
    ) model_i (
        .v_in(v_in_int),
        .v_out(v_out_int),
        .sw1(sw1),
        .sw2(sw2)
    );
endmodule