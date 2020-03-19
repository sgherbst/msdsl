`include "svreal.sv"

module test_table_sim #(
    parameter integer addr_bits=1,
    parameter real real_range=10,
    parameter integer sint_bits=1,
    parameter integer uint_bits=1
) (
    input [(addr_bits-1):0] addr,
    input clk,
    output real real_out,
    output signed [(sint_bits-1):0] sint_out,
    output [(uint_bits-1):0] uint_out
);
    `MAKE_REAL(real_out_int, real_range);
    assign real_out = `TO_REAL(real_out_int);

    model #(
        `PASS_REAL(real_out, real_out_int)
    ) model_i (
        .addr(addr),
        .clk(clk),
        .real_out(real_out_int),
        .sint_out(sint_out),
        .uint_out(uint_out)
    );
endmodule