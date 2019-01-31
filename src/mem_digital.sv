`timescale 1ns / 1ps

`default_nettype none

module mem_digital #(
    parameter init = 0,
    parameter width = 1
) (
    input wire logic [(width-1):0] in,
    output wire logic [(width-1):0] out,
    input wire logic clk,
    input wire logic rst,
    input wire logic cke
);

    // internal state

    logic [(width-1):0] state;

    // create the memory unit

    always @(posedge clk) begin
        if (rst == 1'b1) begin
            state <= init;
        end else if (cke == 1'b1) begin
            state <= in;
        end else begin
            state <= state;
        end
    end

    // assign output 

    assign out = state;
                        
endmodule

`default_nettype wire
