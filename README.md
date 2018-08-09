# Introduction

**msdsl** is a Python3 package for generating real number models (RNMs) from analog circuits.  

# Installation

Cloning the repository, navigate to the top-level directory, and **pip** install the package.

```shell
> git clone https://github.com/sgherbst/msdsl/
> cd msdsl
> pip install -e .
```

# Example

A variety of example circuits are maintained in the **examples/** directory.  In each case, running the example code will produce a real-number model covering the various operating states.

```shell
> cd msdsl/examples
> python buck.py

*********************************** Case 1 ************************************
Switch States
M0: off
D0: off

State Variables
i_L0: 0
dv_dt_C0: -100000.0*output

Output Variables
i_D0: 0
v_D0: -1.0*v_C0
*******************************************************************************

*********************************** Case 2 ************************************
Switch States
M0: on
D0: off

State Variables
di_dt_L0: 100000.0*input - 100000.0*v_C0
dv_dt_C0: 100000.0*i_L0 - 100000.0*output

Output Variables
i_D0: 0
v_D0: -1.0*input
*******************************************************************************

*********************************** Case 3 ************************************
Switch States
M0: off
D0: on

State Variables
di_dt_L0: -100000.0*v_C0
dv_dt_C0: 100000.0*i_L0 - 100000.0*output

Output Variables
i_D0: 1.0*i_L0
v_D0: 0
*******************************************************************************

*********************************** Case 4 ************************************
Switch States
M0: on
D0: on

No solutions found.
*******************************************************************************
```
