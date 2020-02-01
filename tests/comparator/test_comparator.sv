`include "svreal.sv"

module test_comparator (
    input real a,
    input real b,
    output c
);
    `MAKE_REAL(a_int, 10);
    assign `FORCE_REAL(a, a_int);

    `MAKE_REAL(b_int, 100);
    assign `FORCE_REAL(b, b_int);

    model #(
        `PASS_REAL(a, a_int),
        `PASS_REAL(b, b_int)
    ) model_i (
        .a(a_int),
        .b(b_int),
        .c(c)
    );
endmodule