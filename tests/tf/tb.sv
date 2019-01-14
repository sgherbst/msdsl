// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"

`define PROBE (* mark_debug = `"true`" *)

module tb (
    input wire logic clk,
    input wire logic rst
);
    // input is a fixed value
    `PROBE `MAKE_CONST_REAL(1.0, v_in);

    // output has range range +/- 5.0
    `PROBE `MAKE_REAL(v_out, 5.0);

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
    integer f;
    initial begin
        f = $fopen("output.txt", "w");
    end
    always @(posedge clk) begin
        if (rst == 1'b0) begin
            $fwrite(f, "%f\n", `TO_REAL(v_out));
        end
    end
endmodule

