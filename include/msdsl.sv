// Steven Herbst
// sherbst@stanford.edu

// Analog modeling library

`ifndef __MSDSL_SV__
`define __MSDSL_SV__

    `include "real.sv"

    // Convenience functions

    `define DATA_TYPE_DIGITAL(width_expr) \
        logic [((width_expr)-1):0]

    `define GET_FORMAT_DIGITAL(in_name) \
        `DATA_TYPE_DIGITAL($size(in_name))

    `define COPY_FORMAT_DIGITAL(in_name, out_name) \
        `GET_FORMAT_DIGITAL(in_name) out_name

    // Memory

    `define MEM_INTO_ANALOG(in_name, out_name, cke_name, init_expr) \
        mem_analog #( \
            .init(init_expr), \
            `PASS_REAL(in, in_name), \
            `PASS_REAL(out, out_name) \
        ) mem_analog_``out_name``_i ( \
            .in(in_name), \
            .out(out_name), \
            .clk(`EMU_CLK), \
            .rst(`EMU_RST), \
            .cke(cke_name) \
        )

    `define MEM_ANALOG(in_name, out_name, cke_name, init_expr) \
        `COPY_FORMAT_REAL(in_name, out_name); \
        `MEM_INTO_ANALOG(in_name, out_name, cke_name, init_expr)

    `define MEM_INTO_DIGITAL(in_name, out_name, cke_name, init_expr) \
        mem_digital #( \
            .init(init_expr), \
            .width($size(in_name)), \
        ) mem_digital_``out_name``_i ( \
            .in(in_name), \
            .out(out_name), \
            .clk(`EMU_CLK), \
            .rst(`EMU_RST), \
            .cke(cke_name) \
        )

    `define MEM_DIGITAL(in_name, out_name, cke_name, init_expr) \
        `COPY_FORMAT_DIGITAL(in_name, out_name); \
        `MEM_INTO_DIGITAL(in_name, out_name, cke_name, init_expr)

    // Probing waveforms

    `define DUMP_FILE(in_name) \
        initial begin \
            $dumpfile(in_name); \
        end

    `define DUMP_VAR(in_name) \
        initial begin \
            $dumpvars(1, in_name); \
        end

    `define PROBE_NAME(in_name) \
        ``in_name``_probe

    `define MARK_DEBUG \
        mark_debug = `"true`"

    `define MARK_TIME \
        time_signal = `"true`"

    `define MARK_RESET \
        reset_signal = `"true`"

    `define MARK_EXPONENT_REAL(in_name) \
        fp_exponent = `EXPONENT_PARAM_REAL(in_name)

    `define MARK_WIDTH_REAL(in_name) \
        fp_width = `WIDTH_PARAM_REAL(in_name)

    `define PROBE_ANALOG(in_name) \
        `ifdef SIMULATION_MODE \
            real `PROBE_NAME(in_name); \
            `DUMP_VAR(`PROBE_NAME(in_name)) \
            assign `PROBE_NAME(in_name) = `TO_REAL(in_name) \
        `else \
            (* `MARK_DEBUG, `MARK_EXPONENT_REAL(in_name), `MARK_WIDTH_REAL(in_name) *) `GET_FORMAT_REAL(in_name) `PROBE_NAME(in_name); \
            assign `PROBE_NAME(in_name) = in_name \
        `endif

    `define PROBE_TIME(in_name) \
        `ifdef SIMULATION_MODE \
            real `PROBE_NAME(in_name); \
            `DUMP_VAR(`PROBE_NAME(in_name)) \
            assign `PROBE_NAME(in_name) = `TO_REAL(in_name) \
        `else \
            (* `MARK_DEBUG, `MARK_TIME, `MARK_EXPONENT_REAL(in_name), `MARK_WIDTH_REAL(in_name) *) `GET_FORMAT_REAL(in_name) `PROBE_NAME(in_name); \
            assign `PROBE_NAME(in_name) = in_name \
        `endif

    `define PROBE_DIGITAL(in_name) \
        (* `MARK_DEBUG *) `GET_FORMAT_DIGITAL(in_name) `PROBE_NAME(in_name); \
        `ifdef SIMULATION_MODE \
            `DUMP_VAR(`PROBE_NAME(in_name)) \
        `endif \
        assign `PROBE_NAME(in_name) = in_name

    `define PROBE_RESET(in_name) \
        (* `MARK_DEBUG, `MARK_RESET *) logic `PROBE_NAME(in_name); \
        `ifdef SIMULATION_MODE \
            `DUMP_VAR(`PROBE_NAME(in_name)) \
        `endif \
        assign `PROBE_NAME(in_name) = in_name

    // Other macros

    `define ANALOG_ACCUMULATOR(incr_name, out_name, cke_name, init_expr) \
        `ADD_REAL(incr_name, out_name, ``out_name``_next); \
        `MEM_INTO_ANALOG(``out_name``_next, out_name, cke_name, init_expr)

    `define PWM_INTO(duty_expr, freq_expr, out_name) \
        pwm #( \
            .duty(duty_expr), \
            .freq(freq_expr), \
            `PASS_REAL(dt, `EMU_DT) \
        ) pwm_``out_name``_i ( \
            .dt(`EMU_DT), \
            .out(out_name), \
            .clk(`EMU_CLK), \
            .rst(`EMU_RST) \
        )

    `define PWM(duty_expr, freq_expr, out_name) \
        logic out_name; \
        `PWM_INTO(duty_expr, freq_expr, out_name)

`endif