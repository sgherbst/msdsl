# msdsl
[![Actions Status](https://github.com/sgherbst/msdsl/workflows/Regression/badge.svg)](https://github.com/sgherbst/msdsl/actions)
[![Code Coverage](https://codecov.io/gh/sgherbst/msdsl/branch/master/graph/badge.svg)](https://codecov.io/gh/sgherbst/msdsl)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/msdsl.svg)](https://badge.fury.io/py/msdsl)
[![Join the chat at https://gitter.im/sgherbst/msdsl](https://badges.gitter.im/sgherbst/msdsl.svg)](https://gitter.im/sgherbst/msdsl?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

**msdsl** is a tool for generating synthesizable real number models (RNMs) for analog circuits for use in FPGA emulation.  It is part of the mixed-signal emulation framework that include [svreal](https://github.com/sgherbst/svreal) and [anasymod](https://github.com/sgherbst/anasymod).

# Installation

## From PyPI

```shell
> pip install msdsl
```

If you get a permissions error when running the **pip** command, you can try adding the **--user** flag.  This will cause **pip** to install packages in your user directory rather than to a system-wide location.

## From GitHub

If you are a developer of **msdsl**, it is more convenient to clone and install the GitHub repository:

```shell
> git clone https://github.com/sgherbst/msdsl.git
> cd msdsl 
> pip install -e .
```

# Basic example

**msdsl** allows you to describe analog blocks at a variety of abstraction levels.  As a simple example, suppose that you want to model an RC filter with a fixed-timestep equation.  That can be expressed with the following **msdsl** code:

```python
from msdsl import *
from math import exp
r, c, dt = 1e3, 1e-9, 0.1e-6
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
y = m.add_analog_output('y')
a = exp(-dt/(r*c))
m.set_next_cycle(y, a*y + (1-a)*x)
m.compile_and_print(VerilogGenerator())
```

The first thing to notice is that **msdsl** is imported just like any other Python package.  This allows you to instantiate a ``MixedSignalModel`` object that is used to described analog behaviors and generate Verilog code.  Next, an analog input (**x**) and analog output (**y**) are declared.  The ``set_next_cycle`` command implements the discrete-time equation:

```text
y[k+1] = a*y[k] + (1-a)*x[k]
```

Users can specify the clock and reset signals that control the initialization and updating of this equation; they default to macros ``CLK_MSDSL`` and ``RST_MSDSL`` when unspecified.

On the last line, the Verilog code is generated and printed out, resulting in something like this:
```verilog
`include "svreal.sv"
module rc #(
    `DECL_REAL(x),
    `DECL_REAL(y)
) (
    `INPUT_REAL(x),
    `OUTPUT_REAL(y)
);
    // Assign signal: y
    `MUL_CONST_REAL(0.9048374180359596, y, tmp0);
    `MUL_CONST_REAL(0.09516258196404037, x, tmp1);
    `ADD_REAL(tmp0, tmp1, tmp2);
    `DFF_INTO_REAL(tmp2, y, `RST_MSDSL, `CLK_MSDSL, 1'b1, 0);
endmodule
```

This code makes use of macros from [svreal](https://github.com/sgherbst/svreal), which is a library that provides a flexible, synthesizable real-number type.  

Finally, note that although ``compile_and_print`` is used in this example, you may find it more useful to use ``compile_to_file`` in practice, since **msdsl** is often used to generate model files for use in building an emulator.  

# Building models

**msdsl** provides a number of convenient features for building models, such as operator overloading, synthesizable functions, and noise. 

## Signals

**msdsl** signals can be declared as analog or digital, and internal or external.  Digital signals default to 1-bit, unsigned, but their width and signedness can be specified.  Analog signals are real values with a specified +/- range that is used to compute fixed-point formats.  It is generally only necessary to specify ranges for model I/O and state variables, since **msdsl** can automatically figure out the rest.

Here are some examples of signal declarations in **msdsl**:

```python
from msdsl import *
m = MixedSignalModel('model')
a = m.add_analog_input('a')
b = m.add_digital_output('b', signed=True, width=8)
c = m.add_analog_state('c', init=1.23, range_=4.56)
d = m.add_digital_signal('d', width=4)
```

Note the optional ``init`` argument used for state variables.  Although not shown here, it is also available for digital signals.

## Assignments

The two basic types of assignments in **msdsl** are **set_this_cycle** and **set_next_cycle**.  **set_this_cycle** acts like an ``assign`` statement in Verilog, which **set_next_cycle** acts like a synchronous assignment in an ``always`` block.  Here are some examples:

```python
from msdsl import *
m = MixedSignalModel('model')
a = m.add_analog_input('a')
b = m.add_analog_output('b')
c = m.add_analog_state('c', init=1.23, range_=4.56)
m.set_next_cycle(c, 0.9*c + 0.1*a)
d = m.set_this_cycle('d', 6.78*c + 7.89*a)  # create a new signal, 'd'
m.set_this_cycle(b, 0.88*d)  # assign to existing signal 
```

## Operators

Many Python operators for arithmetic, comparison, and bitwise operations are overloaded in **msdsl**, allowing you to write down expressions conveniently.  Currently supported operators include ``+``, ``-``, ``*``, ``~``, ``&``, ``|``, ``^``, ``<<``, `>>`, ``<``, ``>``, ``<=``, ``>=``, ``==``, and ``!=``.  The true division operator, ``/``, is only partially supported: dividing by constants works, but dividing by variables does not.    

## Synthesizable functions

**msdsl** makes it possible to convert Python functions into synthesizable approximations.  Here's an example where that feature is used to implement a variable-timestep RC filter:

```python
import numpy as np
from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc')
x = m.add_analog_input('x')
dt = m.add_analog_input('dt')
y = m.add_analog_output('y')
func = lambda dt: np.exp(-dt/(r*c))
f = m.make_function(func,
    domain=[0, 10*r*c], numel=512, order=1)
a = m.set_from_sync_func('a', f, dt)
x_prev = m.cycle_delay(x, 1)
y_prev = m.cycle_delay(y, 1)
m.set_this_cycle(y, a*y_prev + (1-a)*x_prev)
m.compile_and_print(VerilogGenerator())
```

``func`` is a regular Python function, and it is converted into an **msdsl** ``Function`` via the ``make_function`` command.  This generates a piecewise-polynomial approximation of the function over a specified domain.  In this example, a piecewise-linear approximation is used (``order=1``) with 512 segments (``numel=512``) and the domain is 10 RC time constants (``domain=[0, 10*r*c]``).  By default, inputs outside of the domain will return the value at the closer edge of the domain.

``set_from_sync_func`` generates hardware to implement the function, meaning that ``make_funcion`` can be called once, and then applied multiple times with ``set_from_sync_func``.  This is convenient since it generates more concise output code.

``msdsl`` also supports single-input, multi-output functions.  This is important because it reduces the hardware overhead as compared to completely independent invocations of the same function.  Here's an example: 

```python
import numpy as np
from msdsl import *
m = MixedSignalModel('model')
x = m.add_analog_input('x')
y1 = m.add_analog_output('y1')
y2 = m.add_analog_output('y2')
func1 = lambda t: np.sin(t)
func2 = lambda t: np.cos(t)
f = m.make_function([func1, func2],
    domain=[-np.pi, np.pi], numel=512, order=1)
m.set_from_sync_func([y1, y2], f, x)
m.compile_and_print(VerilogGenerator())  
```

The main difference as compared to the previous example is that ``make_function`` and ``set_from_sync_func`` are called with a list of functions/output variables.

## Pseudorandom noise

**msdsl** provides a means for generating different kinds of pseudorandom noise: uniform, Gaussian, and arbitrary distributions:

```python
from msdsl import *
m = MixedSignalModel('model')

# uniform noise
m.set_this_cycle('a', m.uniform_signal(min_val=-1.23, max_val=4.56))

# Gaussian noise
m.set_gaussian_noise('b', std=1.23, mean=4.56, gen_type=...)

# arbitrary noise distribution
# specify via the inverse cumulative distribution function
inv_cdf = lambda x: ...
inv_cdf_func = m.make_function(inv_cdf, domain=[0.0, 1.0])
m.set_this_cycle('c', m.arbitrary_noise(inv_cdf_func))
```

All noise generators depend on a pseudorandom integer generator, which can be specified with the optional ``gen_type`` parameter (``'lcg'``, ``'mt19937'``, ``'lfsr'``).  The highest-quality generator is MT19937, but it is more resource-intensive, and takes many emulator cycles to start up.  The linear congruential generator (LCG) is an exact implementation of the random number generator called for in the Verilog-2001 specification.  The default is a simple linear feedback shift register (``'lfsr'``).  Random seed values are automatically generated for random number generators, but can be explictly specified as well. 

# Abstraction levels

Up until this point, we have considered the low-level features provided by **msdsl** to implement modeling strategies, but **msdsl** also has a bunch of common model abstractions that are ready to use.

## Differential equations

**msdsl** provides a method for writing down symbolic systems of linear differential equations, which are solved at compile time (i.e., through matrix exponentiation) to produce a simple FPGA implementation.

```python
from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
m.add_eqn_sys([c*Deriv(y) == (x-y)/r])
m.compile_and_print(VerilogGenerator())
```
  
## Switched systems

**msdsl** supports an extension to systems of linear differential equations, in which expressions can take one of several forms, depending on digital inputs.  These expressions are built with the ``eqn_case`` command.  In the example below, a resistor is shorted out by a switch when the digital signal ``s`` is one.  The number of cases can be greater than 2, if the digital select signal has multiple bits. 

```python
from msdsl import *
r, rsw, c = 1e3, 100, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
s = m.add_digital_input('s')
y = m.add_analog_output('y')
g = eqn_case([1/r, 1/r+1/rsw], [s])
m.add_eqn_sys([c*Deriv(y) == (x-y)*g])
m.compile_and_print(VerilogGenerator())
```

## "Netlist"

**msdsl** supports a type of "netlist", where analog components like resistors, capacitors, and inductors are instantiated.  Internally, this generates symbolic KCL and KVL equations, which are solved at compile time using the previously-described differential equation interface.  Switches and diodes are supported in a limited way, in which they are either "ON" or "OFF", changing their Thevenin equivalent representation.  For diodes, additional logic is generated to determine whether the diode is on or off during each timestep. 

The example below is a netlist-style description of an RC filter whose resistor can be shorted out with a switch. 

```python
from msdsl import *
r, rsw, c = 1e3, 100, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
s = m.add_digital_input('s')
y = m.add_analog_output('y')
circ = m.make_circuit()
gnd = circ.make_ground()
circ.capacitor('net_y', gnd, c,
    voltage_range=RangeOf(y))
circ.resistor('net_x', 'net_y', r)
circ.switch('net_x', 'net_y', s, rsw)
circ.voltage('net_x', gnd, x)
circ.add_eqns(AnalogSignal('net_y') == y)
m.compile_and_print(VerilogGenerator())
```

## Transfer function

**msdsl** also allows users to specify analog dynamics with transfer functions.  The user provides the coefficients of numerator and denominator polynomials, using the same style as [cont2discrete](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html).

```python
from msdsl import *
r, c = 1e3, 1e-9
m = MixedSignalModel('rc', dt=0.1e-6)
x = m.add_analog_input('x')
y = m.add_analog_output('y')
m.set_tf(x, y, [[1], [r*c, 1]])
m.compile_and_print(VerilogGenerator())
```

## Templates

We are currently adding higher-level abstractions that represent the function of entire blocks.  This includes a saturation nonlinearity (``SaturationModel``), a lossy-channel, specified from S-parameters (``S4PModel``), and a continuous-time linear equalization model (``CTLEModel``), which is specified by pole/zero values.  These models are implemented using a new variable-timestep discretization developed at Stanford.

```python
from msdsl.templates.saturation import SaturationModel
m1 = SaturationModel(-1, 'dB', module_name='m1')

from msdsl.templates.channel import S4PModel
m2 = S4PModel(s4p_file='myfile.s4p', dtmax=100e-12, module_name='m2')

from msdsl.templates.lds import CTLEModel
m3 = CTLEModel(fz=1e9, fp1=2e9, fp2=10e9, dtmax=100e-12, fmodule_name='m3')
```
