`include "svreal.sv"

module test_eqn_no_dyn (
    input real a,
    output real b
);
    `MAKE_REAL(a_int, 10);
    assign `FORCE_REAL(a, a_int);

    `MAKE_REAL(b_int, 10);
    assign b = `TO_REAL(b_int);

    model #(
        `PASS_REAL(a, a_int),
        `PASS_REAL(b, b_int)
    ) model_i (
        .a(a_int),
        .b(b_int)
    );
endmodule