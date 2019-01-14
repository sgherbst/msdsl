// Steven Herbst
// sherbst@stanford.edu

// Illustrating real number state and the assertion system

`timescale 1ns/1ps

`include "real.sv"

`define PROBE (* mark_debug = `"true`" *)

module tb (
    input wire logic clk,
    input wire logic rst
);
    // input is a fixed value
    `PROBE `MAKE_CONST_REAL(1.0, in);

    // output has range range +/- 1.5
    `PROBE `MAKE_REAL(out, 1.5);

    filter #(
        `PASS_REAL(in, in),
        `PASS_REAL(out, out)
    ) filter_i (
        .in(in),
        .out(out),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    always @(posedge clk) begin
        `PRINT_REAL(out);
    end
endmodule

