// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"
`include "components.sv"
`include "debug.sv"

`default_nettype none

module tb (
    input wire logic clk,
    input wire logic rst
);
    // state variable definitions
    `MAKE_REAL(data, 10.0);

    // gate drive signal
    `COUNTER(2, addr);

    // buck instantiation
    array #(
        `PASS_REAL(data, data)
    ) array_i (
        .addr(addr),
        .data(data),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    `ifdef SIMULATION
        `DUMP_REAL_TO_SCREEN(data);
    `endif
endmodule

`default_nettype wire

