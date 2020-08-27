`include "svreal.sv"

module test_gauss_inv_cdf #(
    parameter real out_range=10
) (
    input [30:0] in_,
    output real out,
    input clk,
    input rst
);
    // wire output
    `MAKE_REAL(out_int, out_range);
    assign out = `TO_REAL(out_int);

    // instantiate model
    model #(
        `PASS_REAL(out, out_int)
    ) model_i (
        .in_(in_),
        .out(out_int),
        .clk(clk),
        .rst(rst)
    );
endmodule