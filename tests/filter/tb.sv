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
    `PROBE `MAKE_CONST_REAL(1.0, v_in);

    // output has range range +/- 1.5
    `PROBE `MAKE_REAL(v_out, 1.5);

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
    always @(posedge clk) begin
        `PRINT_REAL(v_out);
    end
endmodule

