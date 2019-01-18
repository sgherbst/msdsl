`timescale 1ns/1ps

`default_nettype none

module counter #(
    parameter width=1
) (
    input wire logic clk,
    input wire logic rst,
    output var logic [width-1:0] out
);

    always @(posedge clk) begin
        if (rst == 1) begin
            out <= 0;
        end else begin
            out <= out + 1;
        end
    end

endmodule

`default_nettype wire