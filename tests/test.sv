`timescale 1ns/1ps

module test;
    // reset generator
    logic rst = 1'b1;
    
    initial begin
        #1 rst = 1'b0;
    end

    // clock generator
    logic clk=1'b0;
    
    always begin
        #0.5 clk = 1'b1;
        #0.5 clk = 1'b0;
    end

    // instantiate testbench
    tb tb_i(.clk(clk), .rst(rst));
endmodule