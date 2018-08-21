#include "circuit.h"
#include "type_defs.h"

#include <iostream>

using namespace std;

void circuit(input_ap input, output_ap output, bit M0_on, v_out_ap *v_out) {
	//real v_out;

	// State variables
	static local_i_L0_ap local_i_L0;
	static local_v_C0_ap local_v_C0;

	// Diode modes
	static bit D0_on;
	// cout << "Switch:" << M0_on << " ";
	// Dynamic mode number
	ap_uint<2> mode = (D0_on, M0_on);
	// cout << "Mode:" << mode << "D0_on:" << D0_on;

	// State coefficient data
	i_L0_const_ap i_L0_const [] = {0.0, 0.0, 0.0, 0.0};
	v_C0_const_ap v_C0_const [] = {0.0, 0.0, 0.0, 0.0};
	output_to_v_C0_ap output_to_v_C0 [] = {-0.024999999999999998, -0.024999999999999998, -0.024999999999999998, 0.0};
	v_C0_to_v_C0_ap v_C0_to_v_C0 [] = {1.0, 1.0, 1.0, 0.0};
	i_L0_to_i_L0_ap i_L0_to_i_L0 [] = {0.0, 1.0, 1.0, 0.0};
	input_to_i_L0_ap input_to_i_L0 [] = {0.0, 0.024999999999999998, 0.0, 0.0};
	v_C0_to_i_L0_ap v_C0_to_i_L0 [] = {0.0, -0.024999999999999998, -0.024999999999999998, 0.0};
	i_L0_to_v_C0_ap i_L0_to_v_C0 [] = {0.0, 0.024999999999999998, 0.024999999999999998, 0.0};

	// State update equations
	local_i_L0 = i_L0_const[mode] + i_L0_to_i_L0[mode]*local_i_L0 + v_C0_to_i_L0[mode]*local_v_C0 + input_to_i_L0[mode]*input;
	local_v_C0 = v_C0_const[mode] + i_L0_to_v_C0[mode]*local_i_L0 + output_to_v_C0[mode]*output + v_C0_to_v_C0[mode]*local_v_C0;

	// Diode coefficient data
	i_D0_const_ap i_D0_const [] = {0.0, 0.0, 0.0, 0.0};
	v_D0_const_ap v_D0_const [] = {0.0, 0.0, 0.0, 0.0};
	v_C0_to_v_D0_ap v_C0_to_v_D0 [] = {-1.0, 0.0, 0.0, 0.0};
	input_to_v_D0_ap input_to_v_D0 [] = {0.0, -1.0, 0.0, 0.0};
	i_L0_to_i_D0_ap i_L0_to_i_D0 [] = {0.0, 0.0, 1.0, 0.0};

	// Diode update equations
	local_v_D0_ap local_v_D0 = v_D0_const[mode] + v_C0_to_v_D0[mode]*local_v_C0 + input_to_v_D0[mode]*input;
	local_i_D0_ap local_i_D0 = i_D0_const[mode] + i_L0_to_i_D0[mode]*local_i_L0;
	// cout << " i_D:" << local_i_D0 << "\n";

	// Diode D0
	if(D0_on){
		if(local_i_D0 > real(0) || local_i_D0 == real(0)){
			// cout << "Diode off";
			D0_on = 0;
		}
	} else {
		if(local_v_D0 > real(0)){
			D0_on = 1;
		}
	}

	// Output coefficient data
	v_out_const_ap v_out_const [] = {0.0, 0.0, 0.0, 0.0};
	v_C0_to_v_out_ap v_C0_to_v_out [] = {1.0, 1.0, 1.0, 0.0};

	// Output update equations
	*v_out = v_out_const[mode] + v_C0_to_v_out[mode]*local_v_C0;
	// cout << "Internal v_out:" << v_out << "\n";
	//return v_out;
}
