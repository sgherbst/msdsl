#include "circuit.hpp"
#include "vcd.hpp"

#include <iostream>
#include <deque>
#include <stdexcept>
#include <cmath>

using namespace std;

int main() {
	// test bench I/O
	input_type input = 6.6;
	M0_on_type M0_on = 0;
	v_out_type v_out;
	float i_mag;

    header();
    probe({"v_out", "i_mag"});
    long time_ps = 0;

	// Start Test Bench
	for (int i = 0; i < 1000000; i++) {
		// set gate waveform
		if (i % 50 == 0) M0_on = ~M0_on;

		// run one timestep
		circuit(input, M0_on, &v_out, &i_mag);

        // print result
        timestep(time_ps);
        dump("v_out", v_out);
        dump("i_mag", i_mag);
        time_ps += 20000;
	}
}
