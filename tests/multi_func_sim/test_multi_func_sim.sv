`include "svreal.sv"

module test_multi_func_sim #(
    parameter real in_range=10,
    parameter real out_range=10
) (
    input real in_,
    output real out1,
    output real out2,
    input clk,
    input rst
);
    // wire input
    `MAKE_REAL(in_int, in_range);
    assign `FORCE_REAL(in_, in_int);

    // wire out1
    `MAKE_REAL(out1_int, out_range);
    assign out1 = `TO_REAL(out1_int);

    // wire out2
    `MAKE_REAL(out2_int, out_range);
    assign out2 = `TO_REAL(out2_int);

    // instantiate model
    model #(
        `PASS_REAL(in_, in_int),
        `PASS_REAL(out1, out1_int),
        `PASS_REAL(out2, out2_int)
    ) model_i (
        .in_(in_int),
        .out1(out1_int),
        .out2(out2_int),
        .clk(clk),
        .rst(rst)
    );
endmodule