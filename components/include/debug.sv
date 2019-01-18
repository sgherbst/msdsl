`ifndef __DEBUG_SV__
`define __DEBUG_SV__

    `include "real.sv"

    `define DUMP_REAL_TO_FILE(in_name) \
        dump_real_to_file #( \
            `PASS_REAL(in, in_name), \
            .filename(`"``in_name``.txt`") \
        ) dump_real_to_file_``in_name``_i ( \
            .in(in_name), \
            .clk(clk), \
            .rst(rst) \
        )

    `define DUMP_REAL_TO_SCREEN(in_name) \
        dump_real_to_screen #( \
            `PASS_REAL(in, in_name) \
        ) dump_real_to_screen_``in_name``_i ( \
            .in(in_name), \
            .clk(clk), \
            .rst(rst) \
        )

    `define DUMP_VARS(path, filename) \
        initial begin \
            $dumpfile(filename); \
            $dumpvars(0, path); \
        end

`endif