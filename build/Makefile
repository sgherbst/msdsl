# Build flow for 

CIRCUIT_FILE = ../examples/buck.py
VIVADO_HOME = /Volumes/C/Xilinx/Vivado/2018.2/
# VIVADO_HOME = "C:\Xilinx\Vivado\2017.3"

CC = g++
PYTHON = python3
# PYTHON = python

JSON_FILE = circuit.json
CPP_FILE = circuit.cpp
BIN_FILE = circuit

.PHONY: all analyze generate compile run view clean

all: analyze generate compile run view

analyze: 
	$(PYTHON) $(CIRCUIT_FILE) > $(JSON_FILE)

generate: 
	$(PYTHON) ../tools/generate.py $(JSON_FILE) 
#	$(PYTHON) ../tools/generate.py $(JSON_FILE) > $(CPP_FILE)

# TODO...

compile: 

run: 

view: 

clean:
