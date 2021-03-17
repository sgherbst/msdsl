`include "svreal.sv"

`define MAKE_INPUT(k) input real in_``k``
`define MAKE_OUTPUT(k) output real out_``k``

`define PASS_INPUT(k) `PASS_REAL(in_``k``, in_``k``_int)
`define PASS_OUTPUT(k) `PASS_REAL(out_``k``, out_``k``_int)

`define CONNECT_INPUT(k) .in_``k``(in_``k``_int)
`define CONNECT_OUTPUT(k) .out_``k``(out_``k``_int)

`define WIRE_INPUT(k) \
    `MAKE_REAL(in_``k``_int, in_range); \
    assign `FORCE_REAL(in_``k``, in_``k``_int)

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

module test_ctle_interp2 #(
    parameter real in_range=1.5,
    parameter real out_range=1.5
) (
    input real dt,
    `REPLICATE_MACRO_COMMA(MAKE_INPUT),
    `REPLICATE_MACRO_COMMA(MAKE_OUTPUT),
    input clk,
    input rst
);
    // wire inputs
    `REPLICATE_MACRO_SEMICOLON(WIRE_INPUT);

    // wire outputs
    `REPLICATE_MACRO_SEMICOLON(WIRE_OUTPUT);

    // wire dt
    `MAKE_REAL(dt_int, 1.1);
    assign `FORCE_REAL(dt, dt_int);

    // instantiate model
    model #(
        `PASS_REAL(dt, dt_int),
        `REPLICATE_MACRO_COMMA(PASS_INPUT),
        `REPLICATE_MACRO_COMMA(PASS_OUTPUT)
    ) model_i (
        .dt(dt_int),
        `REPLICATE_MACRO_COMMA(CONNECT_INPUT),
        `REPLICATE_MACRO_COMMA(CONNECT_OUTPUT),
        .clk(clk),
        .rst(rst)
    );
endmodule