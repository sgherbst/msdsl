`include "svreal.sv"

module test_binding (
    input real a,
    input real b,
    output real c
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
        .b(b_int)
    );

    // wire internal node to output of fault module
    real c_int;
    assign c = c_int;
    always @(model_i.c) c_int = `TO_REAL(model_i.c);
endmodule