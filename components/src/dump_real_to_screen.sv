`timescale 1ns/1ps

`include "real.sv"
`include "math.sv"

`default_nettype none

module dump_real_to_screen #(
    `DECL_REAL(in)
) (
    `INPUT_REAL(in),
    input wire logic clk,
    input wire logic rst
);

    always @(posedge clk) begin
        if (rst == 1'b0) begin
            `PRINT_REAL(in);
        end
    end

endmodule

`default_nettype none