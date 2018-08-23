# Build flow for generating HLS code from a circuit model

# set Vivado location if not already defined
VIVADO_HOME ?= /Volumes/C/Xilinx/Vivado/2018.2/

# define circuit location
CIRCUIT_FILE = ../../examples/buck.py

# tool binaries
CC = g++
PYTHON = python3

.PHONY: all analyze generate generate_float compile run clean

all: analyze generate compile run
float: analyze generate_float compile run

analyze: 
	$(PYTHON) $(CIRCUIT_FILE) > circuit.json

generate: 
	$(PYTHON) ../../tools/generate.py 

generate_float: 
	$(PYTHON) ../../tools/generate.py --use_float

compile: 
	$(CC) -I$(VIVADO_HOME)/include -I../../msdsl ../../msdsl/vcd.cpp stim.cpp circuit.cpp -o stim

run: 
	./stim > out.vcd

clean: 
	rm -f circuit.json circuit.cpp circuit.hpp stim out.vcd
