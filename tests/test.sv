`timescale 1ns/1ps

module test;
    // reset generator
    logic rst = 1'b1;
    
    initial begin
        #2 rst = 1'b0;
    end

    // clock generator
    logic clk=1'b0;
    
    always begin
        #1 clk = 1'b1;
        #1 clk = 1'b0;
    end

    // instantiate testbench
    tb tb_i(.clk(clk), .rst(rst));
endmodule