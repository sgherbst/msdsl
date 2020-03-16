`include "svreal.sv"

module test_table_sim #(
    parameter integer addr_bits=1,
    parameter real out_range=10
) (
    input [(addr_bits-1):0] addr,
    input clk,
    output real out
);
    `MAKE_REAL(out_int, out_range);
    assign out = `TO_REAL(out_int);

    model #(
        `PASS_REAL(out, out_int)
    ) model_i (
        .addr(addr),
        .clk(clk),
        .out(out_int)
    );
endmodule