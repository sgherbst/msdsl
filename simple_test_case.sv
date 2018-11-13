typedef real real_type; // replaced with actual type

// vio_wiz -- TCL script
// clk_wiz -- TCL script: list of clocks into clock wizard IP
// time_manager -- Magma: same list of clocks into a time manager 
// clock model -- Magma: generates a clock model from a base clock
// prbs -- Verilog
// dut -- Verilog
// dac -- Magma: parameters are #bits and transfer function
// adc -- Magma: parameters are #bits and transfer function
// rc -- Magma: behavioral description -- use msdsl example for starting
// dff -- Verilog
// probing -- TCL script: list of (absolute path, clock domain) that maps to DBG hub and ILA instances for each clock domain

module fpga_tb(
	input sys_clk
);
	logic emu_clk;
	logic rst;

	vio_wiz vio_wiz_i(.emu_clk(emu_clk), .rst(rst));
	clk_wiz clk_wiz_i(.sys_clk(sys_clk), .emu_clk(emu_clk), .tx_clk_en(tx_clk_en), .tx_clk(tx_clk),
		.rx_clk_en(rx_clk_en), .rx_clk(rx_clk));
	time_manager time_manager_i(.dt_tx(dt_tx), .dt_rx(dt_rx), .dt_min(dt_min), .t_emu(t_emu),
		.tx_clk_en(tx_clk_en), .rx_clk_en(rx_clk_en), .emu_clk(emu_clk), .rst(rst));

	my_clk tx_clk_i(.dt_out(dt_tx), .dt_min(dt_min), .emu_clk(emu_clk), .rst(rst));
	my_clk rx_clk_i(.dt_out(dt_rx), .dt_min(dt_min), .emu_clk(emu_clk), .rst(rst));
endmodule

module tb(
	input emu_clk, 
	input tx_clk,
	input rx_clk,
	input rst, 
	input dt_min
);
	prbs prbs_i(.out(tx_data), .clk(tx_clk));
	dut dut_i(.in(tx_data), .out(dut_out), .dt_min(dt_min), .emu_clk(emu_clk), .rst(rst));
	dff dff_i(.in(dut_out), .out(rx_data), .clk(rx_clk));
endmodule

module dut;
	dac(tx_data, rc_in); // ax+b
	rc(rc_in, rc_out); // 
	adc(rc_out, dut_out); // floor(ax+b)
endmodule

// clock implementation
always @(posedge emu_clk) begin
	if (rst == 1'b1)
		dt_out <= T;
	else if (dt_out == dt_in)
		dt_out <= T;
	else	
		dt_out <= dt_out - dt_in;
end

// reset generation: always reset all clock domains while reset is active

// time manager implementation
assign dt_min = min(dt1, dt2, ...);
assign clk_en_1 = ((dt1==dt_min) ? 1'b1 : 1'b0) | rst;
//... repeat for all clocks

always @(posedge emu_clk) begin
	if (rst == 1'b1) begin
		t_emu <= 0'
	end else begin	
		t_emu <= t_emu + dt_min;
	end // end elseend
end // always @(posedge emu_clk)end