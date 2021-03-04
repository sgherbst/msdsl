`include "svreal.sv"

`define MAKE_OUTPUT(k) output real out_``k``
`define PASS_OUTPUT(k) `PASS_REAL(out_``k``, out_``k``_int)
`define CONNECT_OUTPUT(k) .out_``k``(out_``k``_int)

`define WIRE_OUTPUT(k) \
    `MAKE_REAL(out_``k``_int, out_range); \
    assign out_``k`` = `TO_REAL(out_``k``_int)

`define REPLICATE_MACRO_SEMICOLON(name) \
    `name(0); \
    `name(1); \
    `name(2); \
    `name(3)

`define REPLICATE_MACRO_COMMA(name) \
    `name(0), \
    `name(1), \
    `name(2), \
    `name(3)

module test_chan_interp #(
    parameter real in_range=10,
    parameter real out_range=10
) (
    input real dt,
    input real in_,
    `REPLICATE_MACRO_COMMA(MAKE_OUTPUT),
    input clk,
    input rst
);
    // wire input
    `MAKE_REAL(in_int, in_range);
    assign `FORCE_REAL(in_, in_int);

    // wire outputs
    `REPLICATE_MACRO_SEMICOLON(WIRE_OUTPUT);

    // wire dt
    `MAKE_REAL(dt_int, 1e-9);
    assign `FORCE_REAL(dt, dt_int);

    // instantiate model
    model #(
        `PASS_REAL(dt, dt_int),
        `PASS_REAL(in_, in_int),
        `REPLICATE_MACRO_COMMA(PASS_OUTPUT)
    ) model_i (
        .dt(dt_int),
        .in_(in_int),
        `REPLICATE_MACRO_COMMA(CONNECT_OUTPUT),
        .clk(clk),
        .rst(rst)
    );
endmodule