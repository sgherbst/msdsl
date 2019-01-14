# Introduction

**msdsl** is a Python3 package for generating synthesizable real number models (RNMs) from analog circuits.  

# Prerequisites

1. Python 3 must be installed.  (These instructions were tested with Python 3.6.5)
2. Xilinx Vivado must be installed.  (These instructions were tested with Xilinx Vivado 2018.2)
3. **svreal** must be installed (Clone from [https://github.com/sgherbst/svreal.git])

# Path Setup

Two environment variables must be defined: SVREAL_INSTALL_PATH and VIVADO_INSTALL_PATH.  For instructions on defining VIVADO_INSTALL_PATH, see the readme for **svreal**.

To add the SVREAL_INSTALL_PATH environment variable in Windows:

1. Click on the lower-left search bar ("Type here to search"), then type "environment".
2. Click on the option "Edit the system environment variables" that appears.  
3. Click "Environment Variables".
4. In the window that appears, click "New..." under "User variables".
5. In the window that appears, enter "SVREAL_INSTALL_PATH" as the variable name.  For the variable value, enter the path to the top level directory of the cloned **svreal** repository.
6. Click "OK" to close all three of the open windows.

# Installation

Clone the **mdsl** repository, navigate to the top-level directory, and use **pip** to install the package.

```shell
> git clone https://github.com/sgherbst/msdsl/
> cd msdsl
> pip install -e .
```

# Examples

A variety of examples examples are maintained in the **tests/** directory.  All of the tests are run using the script **tests/test.py**.

## tests/hello

This example is just to test whether the simulation environment is set up properly.

```shell
> cd msdsl/tests
> python tests.py -i hello
Hello, world!
```

## tests/filter

This example is a simple first-order low-pass filter.  As shown in line 22 of **tests/filter/gen.py**, the filter dynamics are specified in a single line in the form of a differential equation.  The output printed by this example is the filter's response to a constant input after its output is initialized to zero.

```shell
> cd msdsl/tests
> python tests.py -i filter
v_out = 0.000000
v_out = 0.000000
v_out = 0.333332
v_out = 0.555552
v_out = 0.703699
v_out = 0.802463
v_out = 0.868305
v_out = 0.912200
v_out = 0.941463
v_out = 0.960972
v_out = 0.973977
```
