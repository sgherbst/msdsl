#include "circuit.hpp"
#include "vcd.hpp"

#include <iostream>
#include <stdexcept>
#include <cmath>
#include <vector>

int main() {
    // test bench I/O
    input_type input = 6.6;
    M0_on_type M0_on = 0;
    v_out_type v_out;
    i_mag_type i_mag;

    // create VCD writer
    VcdWriter vcd("out.vcd");

    // write VCD header
    vcd.header();

    // write VCD signal information
    std::vector<std::string> signals;
    signals.push_back("v_out");
    signals.push_back("i_mag");
    vcd.probe(signals);

    // run simulation
    long time_ps = 0;
    for (int i = 0; i < 2000000; i++) {
        // set gate waveform
        if (i % 1000 == 0){
            M0_on = ~M0_on;
        }

        // run one timestep
        circuit(input, M0_on, &v_out, &i_mag);

        // dump result
        vcd.timestep(time_ps);
        vcd.dump<v_out_type>("v_out", v_out);
        vcd.dump<v_out_type>("i_mag", i_mag);

        // increment time
        time_ps += 2000;
    }
}
