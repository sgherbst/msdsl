`include "svreal.sv"

module test_sub (
    input signed [62:0] a,
    input signed [62:0] b,
    output signed [63:0] c
);
    model model_i (
        .a(a),
        .b(b),
        .c(c)
    );
endmodule