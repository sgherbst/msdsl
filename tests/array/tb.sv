// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"

`define PROBE (* mark_debug = `"true`" *)

module tb (
    input wire logic clk,
    input wire logic rst
);
    // state variable definitions
    `PROBE `MAKE_REAL(data, 10.0);

    // gate drive signal
    logic [1:0] addr;

    always @(posedge clk) begin
        if (rst == 1'b1) begin
            addr <= 0;
        end else begin
            addr <= addr + 1;
        end
    end

    // buck instantiation
    array #(
        `PASS_REAL(data, data)
    ) array (
        .addr(addr),
        .data(data),
        .clk(clk),
        .rst(rst)
    );

    // simulation output
    always @(posedge clk) begin
        `PRINT_REAL(data);
    end
endmodule

