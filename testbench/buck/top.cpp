#include "type_defs.h"
#include "circuit.h"
#include "circuit_float.h"
#include <iostream>
#include <deque>
#include <stdexcept>
#include <cmath>

using namespace std;

//TODO:
/*
 * 4. Use more advanced Stimulus ?!?
 * 6. Adapt Generator
 */

int main() {
	// Variables for Test Bench
	bit M0_on;
	double stimulus;
	double input_range[2] = {-400, 400};
	int i;

	// Variables for DUT
	input_ap dut_input = 0.0;
	output_ap dut_output = 0.0;
	v_out_ap dut_init;
	v_out_ap *dut_v_out = &dut_init;

	deque<double> dut_results;

	// Variables for REF
	double ref_input = 0.0;
	double ref_output = 0.0;
	double ref_init;
	double *ref_v_out = &ref_init;

	deque<double> ref_results;

	// Variables for Post-Processing
	deque<double>::iterator results_it;
	deque<double>::iterator postproc_it;

	deque<double> abs_diff;
	double abs_diff_max = 0.0;

	deque<double> rel_diff;
	double rel_diff_max = 0.0;


	// Start Test Bench
	for (i = 0; i < STIMULUS_LEN; i++) {

		// Stimulus Generation
		stimulus = (double) i / STIMULUS_LEN * (input_range[1] - input_range[0]) + input_range[0];

		// Run Simulation
		if (i % 10 == 0) M0_on = !M0_on;

		// DUT fixed
		dut_input = (input_ap) stimulus;
		circuit(dut_input, dut_output, M0_on, dut_v_out);
		dut_results.push_back(*dut_v_out);

		// REF float
		ref_input = stimulus;
		circuit_float(ref_input, ref_output, M0_on, ref_v_out);
		ref_results.push_back(*ref_v_out);
	}

	// Error Calculation
	if (ref_results.size() != dut_results.size())
	{
		throw invalid_argument( "Number of results is not equal between DUT and REF!" );
	}

	for (i = 0; i < ref_results.size(); i++)
	{
		abs_diff.push_back(abs(ref_results[i] - dut_results[i]));
		rel_diff.push_back(100 * abs(1 - (ref_results[i] / dut_results[i])));
	}

	for (postproc_it = abs_diff.begin(); postproc_it != abs_diff.end(); ++postproc_it)
	{
		abs_diff_max = *postproc_it >= abs_diff_max ? *postproc_it : abs_diff_max;
	}

	for (postproc_it = rel_diff.begin(); postproc_it != rel_diff.end(); ++postproc_it)
	{
		rel_diff_max = *postproc_it >= rel_diff_max ? *postproc_it : rel_diff_max;
	}

	cout << "Maximum absolute Deviation            : " << abs_diff_max << "\n";
	cout << "Maximum relative Deviation in Percent : " << rel_diff_max << "\n";
}
