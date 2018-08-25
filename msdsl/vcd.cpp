#include "vcd.hpp"

#include <ctime>

std::string vcd_date_time_string(){
    // ref: https://stackoverflow.com/questions/16357999/current-date-and-time-as-string

    // declarations
    time_t rawtime;
    struct tm* timeinfo;
    char buffer[256];

    // get time
    time (&rawtime);
    timeinfo = localtime(&rawtime);

    // format time using the same date format as Icarus Verilog
    strftime(buffer, sizeof(buffer), "%a %b %d %H:%M:%S %Y", timeinfo);

    // return formatted string
    return std::string(buffer);
}

VcdWriter::VcdWriter(std::string filename){
    current_symbol = 33; // 33 is the minimum allowed VCD character
    file.open(filename);
}

VcdWriter::~VcdWriter(){
    file.close();
}

void VcdWriter::header(){
    // date
    file << "$date" << '\n';
    file << "\t" << vcd_date_time_string() << '\n';
    file << "$end" << '\n';

    // version
    file << "$version" << '\n';
    file << "\tMSDSL" << '\n';
    file << "$end" << '\n';

    // timescale
    file << "$timescale" << '\n';
    file << "\t1ps" << '\n';
    file << "$end" << '\n';
}

void VcdWriter::probe(std::vector<std::string> signals){
    file << "$scope module circuit $end" << '\n';

    for (std::vector<std::string>::iterator it = signals.begin(); it != signals.end(); it++){
        // write variable definition
        file << "$var real 1 " << current_symbol << " " << *it << " $end" << '\n';

        // update signal mapping to link the symbol to the signal name
        signal_mapping[*it] = current_symbol;

        // increment symbol
        current_symbol++;

        // check that the symbol is legal
        if (current_symbol > 126){
            throw std::runtime_error("Invalid VCD symbol.");
        }
    }
    file << "$upscope $end" << '\n';
    file << "$enddefinitions $end" << '\n';
}

void VcdWriter::timestep(long time_ps){
     file << "#" << time_ps << '\n';
}

char VcdWriter::get_signal(std::string signal){
    return signal_mapping[signal];
}