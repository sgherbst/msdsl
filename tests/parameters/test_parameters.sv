`include "svreal.sv"

module test_parameters #(
    parameter param_a=0,
    parameter param_b=0,
    parameter signed [1:0] param_c=0,
    parameter signed [1:0] param_d=0,
    parameter real param_e=0,
    parameter real param_f=0
) (
    input clk,
    input rst,
    output real g
);
    `MAKE_REAL(g_int, 25);
    assign g = `TO_REAL(g_int);

    model #(
        .param_a(param_a),
        .param_b(param_b),
        .param_c(param_c),
        .param_d(param_d),
        .param_e(param_e),
        .param_f(param_f),
        `PASS_REAL(g, g_int)
    ) model_i (
        .clk(clk),
        .rst(rst),
        .g(g_int)
    );
endmodule