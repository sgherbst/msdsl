// Steven Herbst
// sherbst@stanford.edu

// Analog modeling library

`ifndef __COMPONENTS_SV__
`define __COMPONENTS_SV__

    `include "real.sv"

    `define DELAY(tr_expr, tf_expr, dt_expr, in_name, out_name) \
        logic out_name; \
        delay #( \
            .tr(tr_expr), \
            .tf(tf_expr), \
            .dt(dt_expr) \
        ) delay_``out_name``_i ( \
            .in(in_name), \
            .out(out_name), \
            .clk(clk), \
            .rst(rst) \
        )

    `define PWM(duty_expr, freq_expr, dt_expr, out_name) \
        logic out_name; \
        delay #( \
            .tr((1.0-(duty_expr))/(freq_expr)), \
            .tf(1.0*(duty_expr)/(freq_expr)), \
            .dt(dt_expr) \
        ) delay_``out_name``_i ( \
            .in(~out_name), \
            .out(out_name), \
            .clk(clk), \
            .rst(rst) \
        )

    `define MEM_DIGITAL(width_expr, in_name, out_name) \
        mem_digital #( \
            .width(width_expr) \
        ) mem_digital_``out_name``_i ( \
            .in(in_name), \
            .out(out_name), \
            .clk(clk), \
            .rst(rst) \
        )

    `define COUNTER(width_expr, out_name) \
        logic [((width_expr)-1):0] out_name; \
        counter #( \
            .width(width_expr) \
        ) counter_``out_name``_i ( \
            .clk(clk), \
            .rst(rst), \
            .out(out_name) \
        )

`endif