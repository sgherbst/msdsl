`include "svreal.sv"

module test_uniform #(
    parameter real real_range=10
) (
    input clk,
    input rst,
    output real real_out
);
    `MAKE_REAL(real_out_int, real_range);
    assign real_out = `TO_REAL(real_out_int);

    model #(
        `PASS_REAL(real_out, real_out_int)
    ) model_i (
        .clk(clk),
        .rst(rst),
        .real_out(real_out_int)
    );
endmodule