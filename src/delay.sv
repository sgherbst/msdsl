`timescale 1ns/1ps

`include "math.sv"

`default_nettype none

module delay #(
    real tr = 1,
    real tf = 1,
    real dt = 1,
    logic init = 1'b0
) (
    input wire logic in,
    output var logic out,
    input wire logic clk,
    input wire logic rst
);

    // derived parameters

    localparam integer tr_int = int'(tr/dt)-1;
    localparam integer tf_int = int'(tf/dt)-1;
    localparam integer bits = `CLOG2_MATH(`MAX_MATH(tf_int, tr_int) + 1);

    // target value for counter

    wire logic [bits-1:0] target;
    assign target = (in == 1'b1) ? tr_int : tf_int;

    // counter control logic

    var logic [bits-1:0] count;

    always_ff @(posedge clk) begin
        if (rst == 1'b1) begin
            out <= init;
            count <= 'd0;
        end else if ((out == in) || (count == target)) begin
            out <= in;
            count <= 'd0;
        end else begin
            out <= out;
            count <= count + 'd1;
        end
    end

endmodule

`default_nettype wire