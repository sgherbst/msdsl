# Build flow for generating 

# set Vivado location if not already defined
VIVADO_HOME ?= /Volumes/C/Xilinx/Vivado/2018.2/

# define circuit location
CIRCUIT_FILE = ../examples/buck.py

# tool binaries
CC = g++
PYTHON = python3

.PHONY: all analyze generate generate_float clean

all: analyze generate
float: analyze generate_float

analyze: 
	$(PYTHON) $(CIRCUIT_FILE) > circuit.json

generate: 
	$(PYTHON) ../tools/generate.py -i circuit.json -o circuit.cpp

generate_float: 
	$(PYTHON) ../tools/generate.py -i circuit.json -o circuit_float.cpp 

clean: 
	rm -f circuit.json circuit.cpp circuit_float.cpp
