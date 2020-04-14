`include "svreal.sv"

module test_func_sim #(
    parameter real in_range=10,
    parameter real out_range=10
) (
    input real in_,
    output real out,
    input clk,
    input rst
);
    // wire input
    `MAKE_REAL(in_int, in_range);
    assign `FORCE_REAL(in_, in_int);

    // wire output
    `MAKE_REAL(out_int, out_range);
    assign out = `TO_REAL(out_int);

    // instantiate model
    model #(
        `PASS_REAL(in_, in_int),
        `PASS_REAL(out, out_int)
    ) model_i (
        .in_(in_int),
        .out(out_int),
        .clk(clk),
        .rst(rst)
    );
endmodule