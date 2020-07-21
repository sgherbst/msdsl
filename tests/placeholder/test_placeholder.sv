`include "svreal.sv"

module test_placeholder #(
    parameter real in_range=10,
    parameter real out_range=10,
    parameter integer addr_bits=9,
    parameter integer data_bits=18
) (
    input real in_,
    output real out,
    input clk,
    input rst,
    // user configuration controls
    input signed [(data_bits-1):0] wdata0,
    input signed [(data_bits-1):0] wdata1,
    input [(addr_bits-1):0] waddr,
    input we
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
        .rst(rst),
        .wdata0(wdata0),
        .wdata1(wdata1),
        .waddr(waddr),
        .we(we)
    );
endmodule