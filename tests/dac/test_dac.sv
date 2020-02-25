`include "svreal.sv"

module test_dac #(
    parameter integer n_dac=8
) (
    input signed [(n_dac-1):0] d_in,
    output real a_out
);
    `MAKE_REAL(a_out_int, 10);
    assign a_out = `TO_REAL(a_out_int);

    model #(
        `PASS_REAL(a_out, a_out_int)
    ) model_i (
        .d_in(d_in),
        .a_out(a_out_int)
    );
endmodule