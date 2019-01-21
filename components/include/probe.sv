`ifndef __PROBE_SV__
`define __PROBE_SV__

    `include "real.sv"

    // Dumping waveforms for simulation

    `define DUMP_ANALOG(in_name) \
        dump_analog #( \
            `PASS_REAL(in, in_name), \
            .filename(`"``in_name``.txt`") \
        ) dump_analog_``in_name``_i ( \
            .in(in_name), \
            .clk(clk), \
            .rst(rst) \
        )

    // Probing waveforms

    `define PROBE_NAME(in_name) \
        ``in_name``_probe

    `define PROBE_ANALOG(signal) \
        (* mark_debug = `"true`", fp_exponent = `EXPONENT_PARAM_REAL(signal), fp_width = `WIDTH_PARAM_REAL(signal) *) `DATA_TYPE_REAL(`WIDTH_PARAM_REAL(signal)) `PROBE_NAME(signal); \
        assign `PROBE_NAME(signal) = signal \
        `ifdef SIMULATION \
            ; `DUMP_ANALOG(signal) \
        `endif

    `define PROBE_DIGITAL(signal) \
        (* mark_debug = `"true`" *) logic [$size(signal)-1:0] `PROBE_NAME(signal); \
        assign `PROBE_NAME(signal) = signal

`endif