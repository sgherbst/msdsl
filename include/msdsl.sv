// Steven Herbst
// sherbst@stanford.edu

// Analog modeling library

`ifndef __MSDSL_SV__
`define __MSDSL_SV__

    `include "real.sv"

    // Convenience functions

    `define DATA_TYPE_DIGITAL(width_expr) \
        logic [((width_expr)-1):0]

    // Add quotes to a DEFINE parameter
    `define ADD_QUOTES_TO_MACRO(macro) `"macro`"

    // Memory

    `define MEM_INTO_ANALOG(in_name, out_name, cke_name, clk_name, rst_name, init_expr) \
        mem_analog #( \
            .init(init_expr), \
            `PASS_REAL(in, in_name), \
            `PASS_REAL(out, out_name) \
        ) mem_analog_``out_name``_i ( \
            .in(in_name), \
            .out(out_name), \
            .clk(clk_name), \
            .rst(rst_name), \
            .cke(cke_name) \
        )

    `define MEM_ANALOG(in_name, out_name, cke_name, clk_name, rst_name, init_expr) \
        `COPY_FORMAT_REAL(in_name, out_name); \
        `MEM_INTO_ANALOG(in_name, out_name, cke_name, clk_name, rst_name, init_expr)

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

    `define PROBE_ANALOG(in_name) \
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
        `MAKE_GENERIC_REAL(emu_time, `TSTOP_MSDSL, 32); \
        `COPY_FORMAT_REAL(emu_time, emu_time_next); \
        `COPY_FORMAT_REAL(emu_time, emu_time_dt); \
        `ASSIGN_CONST_REAL(`DT_MSDSL, emu_time_dt); \
        `ADD_INTO_REAL(emu_time, emu_time_dt, emu_time_next); \
        `MEM_INTO_ANALOG(emu_time_next, emu_time, 1'b1, `CLK_MSDSL, `RST_MSDSL, 0); \
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
`endif