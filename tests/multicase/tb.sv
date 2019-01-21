// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "components.sv"
`include "probe.sv"

`default_nettype none

module tb (
    input wire logic clk,
    input wire logic rst
);
    // I/O definition
    `MAKE_CONST_REAL(1.0, v_in);
    `MAKE_REAL(v_out, 1.5);

    // gate drive signal
    `PWM(0.50, 300e3, `DT, ctrl);

    // filter instantiation
    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .ctrl(ctrl),
        .clk(clk),
        .rst(rst)
    );

    // emulation output
    `PROBE_ANALOG(v_out);
endmodule

`default_nettype wire