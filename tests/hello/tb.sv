// Steven Herbst
// sherbst@stanford.edu

// Sanity check for simulation

`timescale 1ns/1ps

`include "real.sv"

`default_nettype none

module tb(
    input wire logic clk,
    input wire logic rst
);
    initial begin
        $display("Hello, world!");
        $finish;
    end
endmodule

`default_nettype wire