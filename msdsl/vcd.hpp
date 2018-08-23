#ifndef __VCD_HPP__
#define __VCD_HPP__

#include <vector>

std::string vcd_date_time_string();
void vcd_header();
void vcd_probe(std::vector<std::string> signals);
void vcd_timestep(long time_ps);
char vcd_get_signal(std::string signal);

template <class T> void vcd_dump(std::string signal, T value){
    std::cout << "r" << value << " " << vcd_get_signal(signal) << std::endl;
}

#endif // __VCD_HPP__