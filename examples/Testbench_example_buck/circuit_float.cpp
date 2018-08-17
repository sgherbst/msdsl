#include "circuit_float.h"
#include "type_defs.h"

#include <iostream>

using namespace std;

void circuit_float(double input, double output, bit M0_on, double *d_v_out) {

	// State variables
	static double local_i_L0;
	static double local_v_C0;

	// Diode modes
	static bit D0_on;

	// Dynamic mode number
	ap_uint<2> mode = (D0_on, M0_on);
	// cout << "Mode:" << mode << " D0_on:" << D0_on << "\n";

	// State coefficient data

	double i_L0_const [] = {0.0, 0.0, 0.0, 0.0};
	double v_C0_const [] = {0.0, 0.0, 0.0, 0.0};
	double output_to_v_C0 [] = {-0.024999999999999998, -0.024999999999999998, -0.024999999999999998, 0.0};
	double v_C0_to_v_C0 [] = {1.0, 1.0, 1.0, 0.0};
	double i_L0_to_i_L0 [] = {0.0, 1.0, 1.0, 0.0};
	double input_to_i_L0 [] = {0.0, 0.024999999999999998, 0.0, 0.0};
	double v_C0_to_i_L0 [] = {0.0, -0.024999999999999998, -0.024999999999999998, 0.0};
	double i_L0_to_v_C0 [] = {0.0, 0.024999999999999998, 0.024999999999999998, 0.0};

	// State update equations
	local_i_L0 = i_L0_const[mode] + i_L0_to_i_L0[mode]*local_i_L0 + v_C0_to_i_L0[mode]*local_v_C0 + input_to_i_L0[mode]*input;
	local_v_C0 = v_C0_const[mode] + i_L0_to_v_C0[mode]*local_i_L0 + output_to_v_C0[mode]*output + v_C0_to_v_C0[mode]*local_v_C0;

	// Diode coefficient data
	double i_D0_const [] = {0.0, 0.0, 0.0, 0.0};
	double v_D0_const [] = {0.0, 0.0, 0.0, 0.0};
	double v_C0_to_v_D0 [] = {-1.0, 0.0, 0.0, 0.0};
	double input_to_v_D0 [] = {0.0, -1.0, 0.0, 0.0};
	double i_L0_to_i_D0 [] = {0.0, 0.0, 1.0, 0.0};

	// Diode update equations

	double local_v_D0 = v_D0_const[mode] + v_C0_to_v_D0[mode]*local_v_C0 + input_to_v_D0[mode]*input;
	double local_i_D0 = i_D0_const[mode] + i_L0_to_i_D0[mode]*local_i_L0;
	// cout << " i_D:" << local_i_D0 << "\n";

	// Diode D0
	if(D0_on){
		if(local_i_D0 > double(0) || local_i_D0 == double(0)){
			// cout << "Diode off";
			D0_on = 0;
		}
	} else {
		if(local_v_D0 > double(0)){
			D0_on = 1;
		}
	}

	// Output coefficient data
	double v_out_const [] = {0.0, 0.0, 0.0, 0.0};
	double v_C0_to_v_out [] = {1.0, 1.0, 1.0, 0.0};

	// Output update equations
	*d_v_out = v_out_const[mode] + v_C0_to_v_out[mode]*local_v_C0;

}
