#include "model.hpp"
#include "vcd.hpp"

#include <iostream>
#include <stdexcept>
#include <cmath>
#include <vector>

float random_bit(){
    return (rand()%2 == 0) ? -1.0 : +1.0;
}
int digital_random_bit(){
    return rand()%2;
}

int main() {
    // parameters
    float last_time = 1000e-6;
    float bit_period = 10e-6;
    float digital_bit_period = 100e-6;

    // test bench I/O
    float dt = 0.25e-6;
    float v_in = random_bit();
    int switch_in = digital_random_bit();
    float v_out = 0.0;

    // create VCD writer
    VcdWriter vcd("out.vcd");

    // write VCD header
    vcd.header();

    // write VCD signal information
    vcd.register_real("v_in");
    vcd.register_real("v_out");
    vcd.write_probes();

    // run simulation
    float last_change = 0;
    float digital_last_change = 0;
    for (float time = 0; time <= last_time ; time += dt) {
        // set input state waveform
        if ((time-last_change) > bit_period){
            v_in = random_bit();
            last_change = time;
        }
        if ((time-digital_last_change) > digital_bit_period){
            switch_in = digital_random_bit();
            digital_last_change = time;
        }

        // run one timestep
        model(dt, v_in, switch_in, &v_out);

        // dump result
        vcd.timestep(1e12*time);
        vcd.dump_real<float>("v_in", v_in);
        vcd.dump_real<float>("v_out", v_out);
    }
}
