// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "debug.sv"

`default_nettype none

module tb (
    input wire logic clk,
    input wire logic rst
);
    // input is a fixed value
    `MAKE_CONST_REAL(1.0, v_in);

    // output has range range +/- 5.0
    `MAKE_REAL(v_out, 5.0);

    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `DUMP_REAL_TO_FILE(v_out);
endmodule

`default_nettype wire