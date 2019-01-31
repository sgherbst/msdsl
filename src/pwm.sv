`timescale 1ns / 1ps

`include "real.sv"

`default_nettype none

module pwm #(
    parameter real duty = 0.5,
    parameter real freq = 1e6,
    `DECL_REAL(dt)
) (
    `INPUT_REAL(dt),
    output wire logic out,
    input wire logic clk,
    input wire logic rst
);

    // store the time on and the time off
    localparam real period = 1.0/freq;
    localparam real time_on = (1.0*duty)*period;
    localparam real time_off = (1.0-duty)*period;

    // constants
    `MAKE_CONST_REAL(time_on, time_on_const);
    `MAKE_CONST_REAL(time_off, time_off_const);

    // make a signal to contain acucmulated time
    `MAKE_REAL(time_accum, period);

    // case 1: increment time
    `ADD_REAL(time_accum, dt, incr_by_dt);
    `COPY_FORMAT_REAL(time_accum, incr_by_dt_aligned);
    `ASSIGN_REAL(incr_by_dt, incr_by_dt_aligned);

    // case 2: rewind by on time
    `SUB_REAL(incr_by_dt, time_on_const, rewind_by_on);
    `COPY_FORMAT_REAL(time_accum, rewind_by_on_aligned);
    `ASSIGN_REAL(rewind_by_on, rewind_by_on_aligned);

    // case 3: rewind by off time
    `SUB_REAL(incr_by_dt, time_off_const, rewind_by_off);
    `COPY_FORMAT_REAL(time_accum, rewind_by_off_aligned);
    `ASSIGN_REAL(rewind_by_off, rewind_by_off_aligned);

    // comparisons
    `GT_REAL(time_accum, time_on_const, goto_off);
    `GT_REAL(time_accum, time_off_const, goto_on);

    // create the memory unit
    logic state;

    always @(posedge clk) begin
        if (rst == 1'b1) begin
            state <= 1'b0;
            time_accum <= 0;
        end else if (state == 1'b1) begin
            if (goto_off == 1'b1) begin
                state <= 1'b0;
                time_accum <= rewind_by_on_aligned;
            end else begin
                state <= 1'b1;
                time_accum <= incr_by_dt_aligned;
            end
        end else begin
            if (goto_on == 1'b1) begin
                state <= 1'b1;
                time_accum <= rewind_by_off_aligned;
            end else begin
                state <= 1'b0;
                time_accum <= incr_by_dt_aligned;
            end
        end
    end

    // assign output
    assign out = state;
                        
endmodule

`default_nettype wire
