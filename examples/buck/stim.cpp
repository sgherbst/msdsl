#include "circuit.hpp"
#include "vcd.hpp"

#include <iostream>
#include <stdexcept>
#include <cmath>

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
    vcd.register_real("v_out");
    vcd.register_real("i_mag");
    vcd.register_wire("M0_on");
    vcd.write_probes();

    // run simulation
    long time_ps = 0;
    for (int i = 0; i < 20000; i++) {
        // set gate waveform
        if (i % 1000 == 0){
            M0_on = ~M0_on;
        }

        // run one timestep
        circuit(&i_mag, input, M0_on, &v_out);

        // dump result
        vcd.timestep(time_ps);
        vcd.dump_real<v_out_type>("v_out", v_out);
        vcd.dump_real<i_mag_type>("i_mag", i_mag);
        vcd.dump_wire<M0_on_type>("M0_on", M0_on);

        // increment time
        time_ps += 2000;
    }
}
