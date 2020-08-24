`include "svreal.sv"

module test_var_timestep (
    input real x,
    input real dt,
    output real y,
    input clk,
    input rst
);
    // wire x
    `MAKE_REAL(x_int, 10.0);
    assign `FORCE_REAL(x, x_int);

    // wire dt
    `MAKE_REAL(dt_int, 10e-6);
    assign `FORCE_REAL(dt, dt_int);

    // wire output
    `MAKE_REAL(y_int, 10.0);
    assign y = `TO_REAL(y_int);

    // instantiate model
    model #(
        `PASS_REAL(x, x_int),
        `PASS_REAL(dt, dt_int),
        `PASS_REAL(y, y_int)
    ) model_i (
        .x(x_int),
        .dt(dt_int),
        .y(y_int),
        .clk(clk),
        .rst(rst)
    );
endmodule