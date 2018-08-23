#include "circuit.hpp"
#include "vcd.hpp"

#include <iostream>
#include <deque>
#include <stdexcept>
#include <cmath>
#include <vector>

using namespace std;

int main() {
    bool state = false;

    // test bench I/O
    input_type input;
    v_out_type v_out;

    vcd_header();

    std::vector<std::string> signals;
    signals.push_back("v_out");
    vcd_probe(signals);

    long time_ps = 0;

    // Start Test Bench
    for (int i = 0; i < 1500; i++) {
        // set gate waveform
        if (i % 100 == 0){
            state = !state;
        }

        input = state ? 10 : 0;

        // run one timestep
        circuit(input, &v_out);

        // print result
        vcd_timestep(time_ps);
        vcd_dump<v_out_type>("v_out", v_out);
        time_ps += 10000;
    }
}
