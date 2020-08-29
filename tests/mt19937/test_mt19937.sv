`include "msdsl.sv"

module test_mt19937 (
    input clk,
    input rst,
    input [31:0] seed,
    output [31:0] out
);
    `MT19937_INTO(clk, rst, seed, out);
endmodule