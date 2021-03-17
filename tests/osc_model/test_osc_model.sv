`include "svreal.sv"

module test_osc_model #(
    parameter real period_range = 1e-9
) (
    input real period,
    input real ext_dt,
    output real dt_req,
    output clk_en,
    input clk,
    input rst
);
    // wire period
    `MAKE_REAL(period_int, period_range);
    assign `FORCE_REAL(period, period_int);

    // wire dt_req
    logic [((`DT_WIDTH)-1):0] dt_req_int;
    assign dt_req = (dt_req_int)*(`DT_SCALE);

    // wire emu_dt
    logic [((`DT_WIDTH)-1):0] ext_dt_int;
    assign ext_dt_int = (ext_dt)/(`DT_SCALE);
    logic [((`DT_WIDTH)-1):0] emu_dt;
    assign emu_dt = (ext_dt_int < dt_req_int) ? ext_dt_int : dt_req_int;

    // instantiate MSDSL model, passing through format information
    model #(
        `PASS_REAL(period, period_int)
    ) model_i (
        .period(period_int),
        .dt_req(dt_req_int),
        .emu_dt(emu_dt),
        .clk_en(clk_en),
        .clk(clk),
        .rst(rst)
    );
endmodule