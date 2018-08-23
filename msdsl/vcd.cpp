#include <iostream>
#include <ctime>
#include <map>
#include <vector>

#define VCD_CHAR_MIN 33
#define VCD_CHAR_MAX 126

char vcd_char = VCD_CHAR_MIN;
std::map<std::string, char> signal_mapping;

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

void vcd_header(){
    // date
    std::cout << "$date" << std::endl;
    std::cout << "\t" << vcd_date_time_string() << std::endl;
    std::cout << "$end" << std::endl;

    // version
    std::cout << "$version" << std::endl;
    std::cout << "\tMSDSL" << std::endl;
    std::cout << "$end" << std::endl;

    // timescale
    std::cout << "$timescale" << std::endl;
    std::cout << "\t1ps" << std::endl;
    std::cout << "$end" << std::endl;
}

void vcd_probe(std::vector<std::string> signals){
    std::cout << "$scope module circuit $end" << std::endl;

    for (std::vector<std::string>::iterator it = signals.begin(); it != signals.end(); it++){
        std::cout << "$var real 1 " << vcd_char << " " << *it << " $end" << std::endl;
        signal_mapping[*it] = vcd_char;
        vcd_char++;
    }
    std::cout << "$upscope $end" << std::endl;
    std::cout << "$enddefinitions $end" << std::endl;
}

void vcd_timestep(long time_ps){
    std::cout << "#" << time_ps << std::endl;
}

char vcd_get_signal(std::string signal){
    return signal_mapping[signal];
}