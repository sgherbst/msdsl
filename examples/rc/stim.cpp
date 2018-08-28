#include "circuit.hpp"
#include "vcd.hpp"

#include <iostream>
#include <stdexcept>
#include <cmath>
#include <vector>

int main() {
    // initialize input state
    bool state = false;

    // test bench I/O
    input_type input;
    v_out_type v_out;

    // create VCD writer
    VcdWriter vcd("out.vcd");

    // write VCD header
    vcd.header();

    // write VCD signal information
    vcd.register_real("v_out");
    vcd.register_real("input");
    vcd.write_probes();

    // run simulation
    long time_ps = 0;
    for (int i = 0; i < 1500; i++) {
        // set input state waveform
        if (i % 100 == 0){
            state = !state;
        }

        // select input voltage
        input = state ? 10 : 0;

        // run one timestep
        circuit(input, &v_out);

        // dump result
        vcd.timestep(time_ps);
        vcd.dump_real<v_out_type>("v_out", v_out);
        vcd.dump_real<input_type>("input", input);

        // increment time
        time_ps += 10000;
    }
}
