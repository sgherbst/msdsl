// Steven Herbst
// sherbst@stanford.edu

// Analog modeling library

`ifndef __MSDSL_SV__
`define __MSDSL_SV__

`include "svreal.sv"

// Convenience functions
// TODO: move towards using DATA_TYPE_UINT and DATA_TYPE_SINT

`define DATA_TYPE_DIGITAL(width_expr) \
    logic [((width_expr)-1):0]

`define DATA_TYPE_UINT(width_expr) \
    logic [((width_expr)-1):0]

`define DATA_TYPE_SINT(width_expr) \
    logic signed [((width_expr)-1):0]

// Add quotes to a DEFINE parameter
`define ADD_QUOTES_TO_MACRO(macro) `"macro`"

// Memory

`define MEM_INTO_DIGITAL(in_name, out_name, cke_name, clk_name, rst_name, init_expr, width_expr) \
    mem_digital #( \
        .init(init_expr), \
        .width(width_expr) \
    ) mem_digital_``out_name``_i ( \
        .in(in_name), \
        .out(out_name), \
        .clk(clk_name), \
        .rst(rst_name), \
        .cke(cke_name) \
    )

`define MEM_DIGITAL(in_name, out_name, cke_name, clk_name, rst_name, init_expr, width_expr) \
    `DATA_TYPE_DIGITAL(width_expr) out_name; \
    `MEM_INTO_DIGITAL(in_name, out_name, cke_name, clk_name, rst_name, init_expr, width_expr)

// Synchronous ROM (unsigned integer)

`define SYNC_ROM_INTO_UINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr) \
    sync_rom_uint #( \
        .addr_bits(addr_bits_expr), \
        .data_bits(data_bits_expr), \
        .file_path(file_path_expr) \
    ) sync_rom_uint_``out_name``_i ( \
        .addr(addr_name), \
        .out(out_name), \
        .clk(clk_name), \
        .ce(ce_name) \
    )

`define SYNC_ROM_UINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr) \
    `DATA_TYPE_UINT(data_bits_expr) out_name; \
    `SYNC_ROM_INTO_UINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr)

// Synchronous ROM (signed integer)

// SYNC_ROM_INTO_SINT
// Care has to be taken here to ensure that sign bit extension is used if out_name is wider
// than data_bits_expr.  That's why the output of `SYNC_ROM_UINT is assigned to a temporary
// variable whose width is exactly data_bits_expr; that output is then cast as signed and
// assigned to out_name

`define SYNC_ROM_INTO_SINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr) \
    `SYNC_ROM_UINT(addr_name, zzz_tmp_``out_name``, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr); \
    assign out_name = $signed(zzz_tmp_``out_name``)

// SYNC_ROM_SINT
// Here we can be a bit more direct, because we control the declaration of out_name.  The signal
// out_name is declared as signed and set to have a width of exactly data_bits_expr.  We can then
// directly assign to the signal with SYNC_ROM_UINT (not SYNC_ROM_SINT), avoiding the unnecessary
// declaration of zzz_tmp_``out_name``

`define SYNC_ROM_SINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr) \
    `DATA_TYPE_SINT(data_bits_expr) out_name; \
    `SYNC_ROM_INTO_UINT(addr_name, out_name, clk_name, ce_name, addr_bits_expr, data_bits_expr, file_path_expr)

// Probing waveforms

`define DUMP_VAR(in_name) \
    initial begin \
        #0; \
        $dumpvars(0, in_name); \
    end

`define PROBE_NAME(in_name) \
    ``in_name``_probe

`define MARK_DEBUG \
    mark_debug = `"true`"

`define MARK_TIME \
    time_signal = `"true`"

`define MARK_RESET \
    reset_signal = `"true`"

`define MARK_ANALOG \
    analog_signal = `"true`"

`define MARK_DIGITAL \
    digital_signal = `"true`"

`define MARK_EXPONENT_REAL(in_name) \
    fixed_point_exponent = `EXPONENT_PARAM_REAL(in_name)

`define PROBE_ANALOG_CTRL(in_name, in_name_abspath) \
    `ifdef SIMULATION_MODE_MSDSL \
        real `PROBE_NAME(in_name); \
        `DUMP_VAR(`PROBE_NAME(in_name)) \
        assign `PROBE_NAME(in_name) = `TO_REAL_CTRL(in_name, in_name_abspath) \
    `else \
        (* `MARK_DEBUG, `MARK_ANALOG, `MARK_EXPONENT_REAL(in_name) *) `GET_FORMAT_REAL(in_name) `PROBE_NAME(in_name); \
        assign `PROBE_NAME(in_name) = in_name \
    `endif

    `define TO_REAL_CTRL(name, abs_name) \
    `ifdef FLOAT_REAL \
        name \
    `else \
        (1.0*name) * `POW2_MATH(`EXPONENT_PARAM_REAL(abs_name)) \
    `endif

`define PROBE_ANALOG (in_name) \
    `ifdef SIMULATION_MODE_MSDSL \
        real `PROBE_NAME(in_name); \
        `DUMP_VAR(`PROBE_NAME(in_name)) \
        assign `PROBE_NAME(in_name) = `TO_REAL(in_name) \
    `else \
        (* `MARK_DEBUG, `MARK_ANALOG, `MARK_EXPONENT_REAL(in_name) *) `GET_FORMAT_REAL(in_name) `PROBE_NAME(in_name); \
        assign `PROBE_NAME(in_name) = in_name \
    `endif

`define PROBE_TIME(in_name) \
    `ifdef SIMULATION_MODE_MSDSL \
        real `PROBE_NAME(in_name); \
        `DUMP_VAR(`PROBE_NAME(in_name)) \
        assign `PROBE_NAME(in_name) = `TO_REAL(in_name) \
    `else \
        (* `MARK_DEBUG, `MARK_TIME, `MARK_EXPONENT_REAL(in_name) *) `GET_FORMAT_REAL(in_name) `PROBE_NAME(in_name); \
        assign `PROBE_NAME(in_name) = in_name \
    `endif

`define PROBE_DIGITAL(in_name, width_expr) \
    `ifdef SIMULATION_MODE_MSDSL \
        `DATA_TYPE_DIGITAL(width_expr) `PROBE_NAME(in_name); \
        `DUMP_VAR(`PROBE_NAME(in_name)) \
        assign `PROBE_NAME(in_name) = in_name \
    `else \
        (* `MARK_DEBUG, `MARK_DIGITAL *) `DATA_TYPE_DIGITAL(width_expr) `PROBE_NAME(in_name); \
        assign `PROBE_NAME(in_name) = in_name \
    `endif

`define MAKE_RESET_PROBE \
    `ifdef SIMULATION_MODE_MSDSL \
        logic reset_probe; \
        `DUMP_VAR(reset_probe) \
        assign reset_probe = `RST_MSDSL \
    `else \
        (* `MARK_DEBUG, `MARK_RESET *) logic reset_probe; \
        assign reset_probe = `RST_MSDSL \
    `endif

// Time management
// Note that a emu_time is wider than the default for fixed-point numbers
// The reason is that very high dynamic range is required.
// TODO: avoid using a hard-coded value for the emu_time width

`define MAKE_TIME_PROBE \
    `MAKE_GENERIC_REAL(emu_time, 1.1*`TSTOP_MSDSL, 39); \
    `COPY_FORMAT_REAL(emu_time, emu_time_next); \
    `COPY_FORMAT_REAL(emu_time, emu_time_dt); \
    `ASSIGN_CONST_REAL(`DT_MSDSL, emu_time_dt); \
    `ADD_INTO_REAL(emu_time, emu_time_dt, emu_time_next); \
    `DFF_INTO_REAL(emu_time_next, emu_time, `RST_MSDSL, `CLK_MSDSL, 1'b1, 0.0); \
    `PROBE_TIME(emu_time)

// Decimation counter

`define MAKE_DEC_PROBE \
    logic [(`DEC_BITS_MSDSL-1):0] emu_dec_cnt; \
    logic [(`DEC_BITS_MSDSL-1):0] emu_dec_nxt; \
    logic emu_dec_cmp; \
    assign emu_dec_cmp = (emu_dec_cnt == `DEC_THR_MSDSL) ? 1'b1 : 0; \
    assign emu_dec_nxt = (emu_dec_cmp == 1'b1) ? 'd0 : (emu_dec_cnt + 'd1); \
    `MEM_INTO_DIGITAL(emu_dec_nxt, emu_dec_cnt, 1'b1, `CLK_MSDSL, `RST_MSDSL, 'd0, `DEC_BITS_MSDSL); \
    `ifdef SIMULATION_MODE_MSDSL \
        logic emu_dec_cmp_probe; \
        `DUMP_VAR(emu_dec_cmp_probe) \
        assign emu_dec_cmp_probe = emu_dec_cmp \
    `else \
        (* `MARK_DEBUG, `MARK_DIGITAL *) logic emu_dec_cmp_probe; \
        assign emu_dec_cmp_probe = emu_dec_cmp \
    `endif

//

`define MAKE_EMU_CTRL_PROBES \
    `MAKE_RESET_PROBE; \
    `MAKE_TIME_PROBE; \
    `MAKE_DEC_PROBE

// Other macros

`define PWM_INTO(duty_expr, freq_expr, out_name) \
    `MAKE_CONST_REAL(`DT_MSDSL, dt_``out_name``); \
    pwm #( \
        .duty(duty_expr), \
        .freq(freq_expr), \
        `PASS_REAL(dt, dt_``out_name``) \
    ) pwm_``out_name``_i ( \
        .dt(dt_``out_name``), \
        .out(out_name), \
        .clk(`CLK_MSDSL), \
        .rst(`RST_MSDSL) \
    )

`define PWM(duty_expr, freq_expr, out_name) \
    logic out_name; \
    `PWM_INTO(duty_expr, freq_expr, out_name)

`define EDGE_DET_INTO(in_name, out_name, active_expr, init_expr) \
    edge_det_msdsl #( \
        .init(init_expr), \
        .active(active_expr) \
    ) edge_det_msdsl_``out_name``_i ( \
        .in(in_name), \
        .out(out_name), \
        .clk(`CLK_MSDSL), \
        .rst(`RST_MSDSL) \
    )

`define EDGE_DET(in_name, out_name, active_expr, init_expr) \
    logic out_name; \
    `EDGE_DET_INTO(in_name, out_name, active_expr, init_expr)

`define POSEDGE_INTO(in_name, out_name) \
    `EDGE_DET_INTO(in_name, out_name, 1, 0)

`define POSEDGE(in_name, out_name) \
    `EDGE_DET(in_name, out_name, 1, 0)

`define NEGEDGE_INTO(in_name, out_name) \
    `EDGE_DET_INTO(in_name, out_name, 0, 1)

`define NEGEDGE(in_name, out_name) \
    `EDGE_DET(in_name, out_name, 0, 1)

// pseudorandom number generation

`define LCG_MSDSL_INTO(clk_name, rst_name, cke_name, seed_name, out_name) \
    lcg_msdsl lcg_msdsl_``out_name`` ( \
        .clk(``clk_name``), \
        .rst(``rst_name``), \
        .cke(``cke_name``), \
        .seed(``seed_name``), \
        .out(``out_name``) \
    )

`define LCG_MSDSL(clk_name, rst_name, cke_name, seed_name, out_name) \
    logic [31:0] ``out_name``; \
    `LCG_MSDSL_INTO(``clk_name``, ``rst_name``, ``cke_name``, ``seed_name``, ``out_name``)

`define MT19937_INTO(clk_name, rst_name, cke_name, seed_name, out_name) \
    mt19937_wrapper mt19937_``out_name`` ( \
        .clk(``clk_name``), \
        .rst(``rst_name``), \
        .cke(``cke_name``), \
        .seed(``seed_name``), \
        .out(``out_name``) \
    )

`define MT19937(clk_name, rst_name, cke_name, seed_name, out_name) \
    logic [31:0] ``out_name``; \
    `MT19937_INTO(``clk_name``, ``rst_name``, ``cke_name``, ``seed_name``, ``out_name``)

/////////////////////////////////////////////////
// Module implementations are defined below...
/////////////////////////////////////////////////

// Edge detector

module edge_det_msdsl #(
	parameter init = 0,
    parameter active = 1
) (
    input wire logic in,
    output wire logic out,
    input wire logic clk,
    input wire logic rst
);

	// internal state
	logic last;
	always @(posedge clk) begin
		if (rst == 1'b1) begin
			last <= init;
		end else begin
			last <= in;
		end
	end

	// output assignment
	assign out = ((last == (1-active)) && (in == active)) ? 1'b1 : 1'b0;

endmodule

// Generic DFF

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

// Synchronous ROM (unsigned integer)

module sync_rom_uint #(
    parameter integer addr_bits=1,
    parameter integer data_bits=1,
    parameter file_path=""
) (
    input wire logic [(addr_bits-1):0] addr,
    output wire logic [(data_bits-1):0] out,
    input wire logic clk,
    input wire logic ce
);
    // load the ROM
    logic [(data_bits-1):0] rom [0:((2**addr_bits)-1)];
    initial begin
        $readmemb(file_path, rom);
    end

    // read from the ROM
    logic [(data_bits-1):0] data;
    always @(posedge clk) begin
        if (ce) begin
            data <= rom[addr];
        end
    end

    // assign to the output
    assign out = data;
endmodule

// PWM model

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

// Linear congruential generator, using the equation
// defined in IEEE-1364-2001, pp. 318-319

module lcg_msdsl (
    input clk,
    input rst,
    input cke,
    input [31:0] seed,
    output reg [31:0] out
);
    always @(posedge clk) begin
        if (rst) begin
            out <= seed;
        end else if (cke) begin
            out <= (32'd69069 * out) + 32'd1;
        end else begin
            out <= out;
        end
    end
endmodule

////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
//////////////////// start of of verilog-mersenne by alexforencich
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////

/*
Copyright (c) 2014-2016 Alex Forencich
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

// Language: Verilog 2001

`timescale 1ns / 1ps

/*
 * AXI4-Stream MT19937 Mersenne Twister
 */
module axis_mt19937
(
    input  wire         clk,
    input  wire         rst,

    /*
     * AXI output
     */
    output wire [31:0]  output_axis_tdata,
    output wire         output_axis_tvalid,
    input  wire         output_axis_tready,

    /*
     * Status
     */
    output wire         busy,

    /*
     * Configuration
     */
    input  wire [31:0]  seed_val,
    input  wire         seed_start
);

// state register
localparam [1:0]
    STATE_IDLE = 2'd0,
    STATE_SEED = 2'd1;

reg [1:0] state_reg = STATE_IDLE, state_next;

reg [31:0] mt [623:0];
reg [31:0] mt_save_reg = 0, mt_save_next;
reg [9:0] mti_reg = 625, mti_next;

reg [31:0] y1, y2, y3, y4, y5;

reg [9:0] mt_wr_ptr;
reg [31:0] mt_wr_data;
reg mt_wr_en;

reg [9:0] mt_rd_a_ptr_reg = 0, mt_rd_a_ptr_next;
reg [31:0] mt_rd_a_data = 0;

reg [9:0] mt_rd_b_ptr_reg = 0, mt_rd_b_ptr_next;
reg [31:0] mt_rd_b_data = 0;

reg [31:0] product_reg = 0, product_next;
reg [31:0] factor1_reg = 0, factor1_next;
reg [31:0] factor2_reg = 0, factor2_next;
reg [4:0] mul_cnt_reg = 0, mul_cnt_next;

reg [31:0] output_axis_tdata_reg = 0, output_axis_tdata_next;
reg output_axis_tvalid_reg = 0, output_axis_tvalid_next;

reg busy_reg = 0;

assign output_axis_tdata = output_axis_tdata_reg;
assign output_axis_tvalid = output_axis_tvalid_reg;

assign busy = busy_reg;

always @* begin
    state_next = 2'bz;

    mt_save_next = mt_save_reg;
    mti_next = mti_reg;

    mt_wr_data = 0;
    mt_wr_ptr = 0;
    mt_wr_en = 0;

    y1 = 32'bz;
    y2 = 32'bz;
    y3 = 32'bz;
    y4 = 32'bz;
    y5 = 32'bz;

    mt_rd_a_ptr_next = mt_rd_a_ptr_reg;
    mt_rd_b_ptr_next = mt_rd_b_ptr_reg;

    product_next = product_reg;
    factor1_next = factor1_reg;
    factor2_next = factor2_reg;
    mul_cnt_next = mul_cnt_reg;

    output_axis_tdata_next = output_axis_tdata_reg;
    output_axis_tvalid_next = output_axis_tvalid_reg & ~output_axis_tready;

    case (state_reg)
        STATE_IDLE: begin
            // idle state
            if (seed_start) begin
                mt_save_next = seed_val;
                product_next = 0;
                factor1_next = mt_save_next ^ (mt_save_next >> 30);
                factor2_next = 32'd1812433253;
                mul_cnt_next = 31;
                mt_wr_data = mt_save_next;
                mt_wr_ptr = 0;
                mt_wr_en = 1;
                mti_next = 1;
                state_next = STATE_SEED;
            end else if (output_axis_tready) begin
                if (mti_reg == 625) begin
                    mt_save_next = 32'd5489;
                    product_next = 0;
                    factor1_next = mt_save_next ^ (mt_save_next >> 30);
                    factor2_next = 32'd1812433253;
                    mul_cnt_next = 31;
                    mt_wr_data = mt_save_next;
                    mt_wr_ptr = 0;
                    mt_wr_en = 1;
                    mti_next = 1;
                    state_next = STATE_SEED;
                end else begin
                    if (mti_reg < 623)
                        mti_next = mti_reg + 1;
                    else
                        mti_next = 0;

                    if (mt_rd_a_ptr_reg < 623)
                        mt_rd_a_ptr_next = mt_rd_a_ptr_reg + 1;
                    else
                        mt_rd_a_ptr_next = 0;

                    if (mt_rd_b_ptr_reg < 623)
                        mt_rd_b_ptr_next = mt_rd_b_ptr_reg + 1;
                    else
                        mt_rd_b_ptr_next = 0;

                    mt_save_next = mt_rd_a_data;
                    y1 = {mt_save_reg[31], mt_rd_a_data[30:0]};
                    y2 = mt_rd_b_data ^ (y1 >> 1) ^ (y1[0] ? 32'h9908b0df : 32'h0);
                    y3 = y2 ^ (y2 >> 11);
                    y4 = y3 ^ ((y3 << 7) & 32'h9d2c5680);
                    y5 = y4 ^ ((y4 << 15) & 32'hefc60000);
                    output_axis_tdata_next = y5 ^ (y5 >> 18);
                    output_axis_tvalid_next = 1;
                    mt_wr_data = y2;
                    mt_wr_ptr = mti_reg;
                    mt_wr_en = 1;
                    state_next = STATE_IDLE;
                end
            end else begin
                state_next = STATE_IDLE;
            end
        end
        STATE_SEED: begin
            if (mul_cnt_reg == 0) begin
                if (mti_reg < 624) begin
                    //mt_save_next = 32'd1812433253 * (mt_save_reg ^ (mt_save_reg >> 30)) + mti_reg;
                    mt_save_next = product_reg + mti_reg;
                    product_next = 0;
                    factor1_next = mt_save_next ^ (mt_save_next >> 30);
                    factor2_next = 32'd1812433253;
                    mul_cnt_next = 31;
                    mt_wr_data = mt_save_next;
                    mt_wr_ptr = mti_reg;
                    mt_wr_en = 1;
                    mti_next = mti_reg + 1;
                    mt_rd_a_ptr_next = 0;
                    state_next = STATE_SEED;
                end else begin
                    mti_next = 0;
                    mt_save_next = mt_rd_a_data;
                    mt_rd_a_ptr_next = 1;
                    mt_rd_b_ptr_next = 397;
                    state_next = STATE_IDLE;
                end
            end else begin
                mul_cnt_next = mul_cnt_reg - 1;
                factor1_next = factor1_reg << 1;
                factor2_next = factor2_reg >> 1;
                if (factor2_reg[0]) product_next = product_reg + factor1_reg;
                state_next = STATE_SEED;
            end
        end
    endcase
end

always @(posedge clk) begin
    if (rst) begin
        state_reg <= STATE_IDLE;
        mti_reg <= 625;
        mt_rd_a_ptr_reg <= 0;
        mt_rd_b_ptr_reg <= 0;
        product_reg <= 0;
        factor1_reg <= 0;
        factor2_reg <= 0;
        mul_cnt_reg <= 0;
        output_axis_tdata_reg <= 0;
        output_axis_tvalid_reg <= 0;
        busy_reg <= 0;
    end else begin
        state_reg <= state_next;

        mt_save_reg = mt_save_next;
        mti_reg <= mti_next;

        mt_rd_a_ptr_reg <= mt_rd_a_ptr_next;
        mt_rd_b_ptr_reg <= mt_rd_b_ptr_next;

        product_reg <= product_next;
        factor1_reg <= factor1_next;
        factor2_reg <= factor2_next;
        mul_cnt_reg <= mul_cnt_next;

        output_axis_tdata_reg <= output_axis_tdata_next;
        output_axis_tvalid_reg <= output_axis_tvalid_next;

        busy_reg <= state_next != STATE_IDLE;

        if (mt_wr_en) begin
            mt[mt_wr_ptr] <= mt_wr_data;
        end

        mt_rd_a_data <= mt[mt_rd_a_ptr_next];
        mt_rd_b_data <= mt[mt_rd_b_ptr_next];

    end
end

endmodule

////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////
//////////////////// end of verilog-mersenne by alexforencich
////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////

module mt19937_wrapper (
    input wire logic clk,
    input wire logic rst,
    input wire logic cke,
    input wire logic [31:0] seed,
    output wire logic [31:0] out
);
    // internal signals
    logic [31:0] tdata;
    logic tvalid;
    logic busy;
    logic seed_start;

    // instantiate MT19937 core
    axis_mt19937 axis_mt19937_i (
        .clk(clk),
        .rst(rst),
        .output_axis_tdata(tdata),
        .output_axis_tvalid(tvalid),
        .output_axis_tready(cke),
        .busy(busy),
        .seed_val(seed),
        .seed_start(seed_start)
    );

    // assign output
    assign out = (tvalid & (!busy)) ? tdata : 32'h00000000;

    // manage seed_start signal
    // seeding happens upon reset
    logic has_started;
    always @(posedge clk) begin
        if (rst) begin
            seed_start <= 1'b0;
            has_started <= 1'b0;
        end else if (!has_started) begin
            seed_start <= 1'b1;
            has_started <= 1'b1;
        end else begin
            seed_start <= 1'b0;
            has_started <= 1'b1;
        end
    end
endmodule


`endif // `ifndef __MSDSL_SV__