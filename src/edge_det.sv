``timescale 1ns / 1ps

`default_nettype none

module edge_det #(
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
	assign out = (last == (~active)) && (in == active) ? 1'b1 : 1'b0;
                        
endmodule

`default_nettype wire
