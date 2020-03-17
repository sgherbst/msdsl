`include "svreal.sv"

module test_adc #(
    parameter integer n_adc=8
) (
    input real a_in,
    output signed [(n_adc-1):0] d_out
);
    `MAKE_REAL(a_in_int, 10);
    assign `FORCE_REAL(a_in, a_in_int);

    model #(
        `PASS_REAL(a_in, a_in_int)
    ) model_i (
        .a_in(a_in_int),
        .d_out(d_out)
    );
endmodule