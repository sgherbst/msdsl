#include "vcd.hpp"

#include <ctime>
#include <utility>

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

void VcdWriter::register_name(std::string name){
    name_to_symbol[name] = current_symbol;
    current_symbol++;

    if (current_symbol > 126){
        throw std::runtime_error("Invalid symbol.");
    }
}

void VcdWriter::register_real(std::string name){
    register_name(name);
    real_signals.push_back(RealSignal(name));
}

void VcdWriter::register_wire(std::string name, int length){
    register_name(name);
    wire_signals.push_back(WireSignal(name, length));
}

void VcdWriter::write_probes(){
    // start probes section
    file << "$scope module circuit $end" << '\n';

    // real signals
    for (std::vector<RealSignal>::iterator it = real_signals.begin(); it != real_signals.end(); it++){
        std::string name = it->name;
        char symbol = name_to_symbol[name];

        file << "$var real 1 " << symbol << " " << name << " $end" << '\n';
    }

    // wire signals
    for (std::vector<WireSignal>::iterator it = wire_signals.begin(); it != wire_signals.end(); it++){
        std::string name = it->name;
        char symbol = name_to_symbol[name];

        file << "$var wire " << it->width << " " << symbol << " " << name;

        if (it->width > 1){
            file << (" [" + std::to_string((it->width)-1) + ":0]");
        }

        file << " $end" << '\n';
    }

    // end probes section
    file << "$upscope $end" << '\n';
    file << "$enddefinitions $end" << '\n';
}

void VcdWriter::timestep(long time_ps){
     file << "#" << time_ps << '\n';
}