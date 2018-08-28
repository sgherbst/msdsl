#ifndef __VCD_HPP__
#define __VCD_HPP__

#include "ap_int.h"
#include "ap_fixed.h"

#include <iostream>
#include <fstream>
#include <map>
#include <vector>
#include <utility>

struct RealSignal{
    std::string name;
    RealSignal(std::string name) : name(name) {}
};

struct WireSignal{
    std::string name;
    int width;
    WireSignal(std::string name, int width) : name(name), width(width) {}
};

class VcdWriter{
    private:
        std::ofstream file;
        std::map<std::string, char> name_to_symbol;
        std::vector<RealSignal> real_signals;
        std::vector<WireSignal> wire_signals;
        char current_symbol;
        void register_name(std::string name);
    public:
        VcdWriter(std::string filename);
        ~VcdWriter();
        void header();
        void register_real(std::string name);
        void register_wire(std::string name, int length=1);
        void write_probes();
        void timestep(long time_ps);

        // templated methods
        template <class T> void dump_real(std::string name, T data) {
            file << "r" << data << " " << name_to_symbol[name] << '\n';
        }
        template <class T> void dump_wire(std::string name, T data) {
            // note that the arbitrary precision type already places "0b" at the front of the string,
            // so we need to remove the leading zero to be compatible with the VCD format
            file << data.to_string(2).substr(1) << " " << name_to_symbol[name] << '\n';
        }
};

#endif // __VCD_HPP__