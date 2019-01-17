// Steven Herbst
// sherbst@stanford.edu

`timescale 1ns/1ps

`include "real.sv"

`define PROBE (* mark_debug = `"true`" *)

module tb (
    input wire logic clk,
    input wire logic rst
);
    // I/O definition
    `PROBE `MAKE_CONST_REAL(1.0, v_in);
    `PROBE `MAKE_REAL(v_out, 1.5);

    // gate drive signal
    localparam COUNT_BITS = 5;
    logic [COUNT_BITS-1:0] count;

    always @(posedge clk) begin
        if (rst == 1'b1) begin
            count <= 0;
        end else begin
            count <= count + 1;
        end
    end

    // filter instantiation
    filter #(
        `PASS_REAL(v_in, v_in),
        `PASS_REAL(v_out, v_out)
    ) filter_i (
        .v_in(v_in),
        .v_out(v_out),
        .ctrl(count[COUNT_BITS-1]),
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

