`timescale 1ns/1ps

`include "math.sv"

`default_nettype none

module mem_digital #(
    init = 0,
    width = 1
) (
    input wire logic [width-1:0] in,
    output var logic [width-1:0] out,
    input wire logic clk,
    input wire logic rst
);

    always_ff @(posedge clk) begin
        if (rst == 1'b1) begin
            out <= init;
        end else begin
            out <= in;
        end
    end

endmodule

`default_nettype wire