#ifndef __VCD_HPP__
#define __VCD_HPP__

#include <iostream>
#include <fstream>
#include <map>
#include <vector>

class VcdWriter{
    private:
        std::ofstream file;
        std::map<std::string, char> signal_mapping;
        char get_signal(std::string signal);
        char current_symbol;
    public:
        VcdWriter(std::string filename);
        ~VcdWriter();
        void header();
        void probe(std::vector<std::string> signals);
        void timestep(long time_ps);
        template <class T> void dump(std::string signal, T value){
            // it seems simplest to define a templated method in a file
            file << "r" << value << " " << get_signal(signal) << '\n';
        }
};

#endif // __VCD_HPP__