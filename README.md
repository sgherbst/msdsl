# Introduction

**msdsl** is a Python3 package for generating synthesizable real number models (RNMs) from analog circuits.  

# Prerequisites

1. Python 3 must be installed.  (These instructions were tested with Python 3.6.5)
2. Xilinx Vivado must be installed.  (These instructions were tested with Xilinx Vivado 2018.2)
3. **svreal** must be installed (Clone it from [https://github.com/sgherbst/svreal.git](https://github.com/sgherbst/svreal.git))

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