// Steven Herbst
// sherbst@stanford.edu

// Sanity check for simulation

`timescale 1ns/1ps

module tb(
    input wire logic clk,
    input wire logic rst
);
    initial begin
        $display("Hello, world!");
    end
endmodule
