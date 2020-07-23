`include "svreal.sv"

module test_gaussian_noise #(
    parameter real real_range=10
) (
    input clk,
    input rst,
    input real mean_in,
    input real std_in,
    output real real_out
);
    `MAKE_REAL(mean_int, real_range);
    assign `FORCE_REAL(mean_in, mean_int);

    `MAKE_REAL(std_int, real_range);
    assign `FORCE_REAL(std_in, std_int);

    `MAKE_REAL(real_out_int, real_range);
    assign real_out = `TO_REAL(real_out_int);

    model #(
        `PASS_REAL(mean_in, mean_int),
        `PASS_REAL(std_in, std_int),
        `PASS_REAL(real_out, real_out_int)
    ) model_i (
        .clk(clk),
        .rst(rst),
        .mean_in(mean_int),
        .std_in(std_int),
        .real_out(real_out_int)
    );
endmodule