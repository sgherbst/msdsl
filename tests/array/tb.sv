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
    // state variable definitions
    `MAKE_REAL(data, 10.0);

    // gate drive signal
    `COUNTER(2, addr);

    // array instantiation
    array #(
        `PASS_REAL(data, data)
    ) array_i (
        .addr(addr),
        .data(data),
        .clk(clk),
        .rst(rst)
    );

    // emulation output
    `PROBE_ANALOG(data);
endmodule

`default_nettype wire

