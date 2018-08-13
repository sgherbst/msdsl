import sys
from msdsl.util import from_json

def local(var):
    return 'local_' + var

def on(comp):
    return comp + '_on'

def mode2int(dyn_modes, dyn_indices):
    retval = 0
    for name, mode in dyn_modes.items():
        if mode == 'on':
            retval += (1<<dyn_indices[name])
    return retval

def to(a, b):
    return a + '_to_' + b

def const(x):
    return x + '_const'

def array(arr):
    return '{' + ', '.join(str(x if x != -0.0 else 0.0) for x in arr) + '}'

def mode():
    return 'mode'

def at_mode():
    return '[' + mode() + ']'

def update_from_expr(case_no, n_modes, value, expr, coeff_data, input_vars):
    if const(value) not in coeff_data:
        coeff_data[const(value)] = [0] * n_modes
    coeff_data[const(value)][case_no] = expr['const']

    for var_name, var_coeff in expr['vars'].items():
        input_vars[value].add(var_name)
        if to(var_name, value) not in coeff_data:
            coeff_data[to(var_name, value)] = [0] * n_modes
        coeff_data[to(var_name, value)][case_no] = var_coeff

file_name = sys.argv[1]
file_text = open(file_name, 'r').read()

circuit = from_json(file_text)

# include files
print('#include "ap_int.h"')
print('#include "ap_fixed.h"')
print()

# declare types
print('typedef ap_fixed<24, 12> real; // placeholder!')
print('typedef ap_fixed<24,12> coeff; // placeholder!')
print('typedef ap_uint<1> bit;')
print()

# declare function
print('void circuit(', end='')
io = []
io += ['real ' + ext_sym for ext_sym in circuit['ext_syms']]
io += ['bit ' + on(mosfet) for mosfet in circuit['mosfets']]
io += ['real *' + output for output in circuit['outputs']]
print(', '.join(io), end='')
print(') {')

# declare state variables
print('\t// State variables')
for state in circuit['states']:
    print('\tstatic real ' + local(state) + ';')
print()

# declare diode modes
print('\t// Diode modes')
for diode in circuit['diodes'].keys():
    print('\tstatic bit ' + on(diode) + ';')
print()

# create the mode variable
dyn_comps = list(circuit['diodes'].keys()) + circuit['mosfets']
dyn_indices = {comp : idx for idx, comp in enumerate(reversed(dyn_comps))}

n_modes = 1 << len(dyn_comps)

# print mode variable
print('\t// Dynamic mode number')
print('\tap_uint<' + str(len(dyn_comps)) + '> ' + mode() + ' = (' + ', '.join(on(comp) for comp in dyn_comps) +');')
print()

# create the coefficient data
state_coeff_data = {}
state_input_vars = {state:set() for state in circuit['states']}
for case in circuit['cases']:
    case_no = mode2int(case['dyn_modes'], dyn_indices)
    for state, expr in case['states'].items():
        update_from_expr(case_no, n_modes, state, expr, state_coeff_data, state_input_vars)

# print the coefficient data
print('\t// State coefficient data')
for coeff_name, coeff_array in state_coeff_data.items():
    print('\tcoeff ' + coeff_name + ' [] = ' + array(coeff_array) + ';')
print()

# print the update equations
ext_set = set(circuit['ext_syms'])
print('\t// State update equations')
for state, vars in state_input_vars.items():
    print('\t' + local(state) + ' = ', end='')
    update = []
    update.append(const(state)+at_mode())
    for var in vars:
        var_name = local(var) if var not in ext_set else var
        update.append(to(var, state) + at_mode() + '*' + var_name)
    print(' + '.join(update) + ';')
print()

# build data for diode equations
diode_coeff_data = {}
diode_input_vars = {}
diode_input_vars.update({diode['v']:set() for diode in circuit['diodes'].values()})
diode_input_vars.update({diode['i']:set() for diode in circuit['diodes'].values()})
for case in circuit['cases']:
    case_no = mode2int(case['dyn_modes'], dyn_indices)
    for diode, values in case['diodes'].items():
        for value, expr in values.items():
            update_from_expr(case_no, n_modes, value, expr, diode_coeff_data, diode_input_vars)

# print the diode coefficient data
print('\t// Diode coefficient data')
for coeff_name, coeff_array in diode_coeff_data.items():
    print('\tcoeff ' + coeff_name + ' [] = ' + array(coeff_array) + ';')
print()

# print the diode equations
print('\t// Diode update equations')
for value, vars in diode_input_vars.items():
    print('\treal ' + local(value) + ' = ', end='')
    update = []
    update.append(const(value)+at_mode())
    for var in vars:
        var_name = local(var) if var not in ext_set else var
        update.append(to(var, value) + at_mode() + '*' + var_name)
    print(' + '.join(update) + ';')
print()

# diode decisions
for diode, props in circuit['diodes'].items():
    print('\t// Diode ' + diode)
    print('\tif('+on(diode)+'){')
    print('\t\tif(' + local(props['i']) + ' < real(0)){')
    print('\t\t\t' + on(diode) + ' = 0;')
    print('\t\t}')
    print('\t} else {')
    print('\t\tif(' + local(props['v']) + ' > real(' + str(props['vf']) + ')){')
    print('\t\t\t' + on(diode) + ' = 1;')
    print('\t\t}')
    print('\t}')
    print()

# build data for output equations
output_coeff_data = {}
output_input_vars = {state:set() for state in circuit['outputs']}
for case in circuit['cases']:
    case_no = mode2int(case['dyn_modes'], dyn_indices)
    for output, expr in case['outputs'].items():
        update_from_expr(case_no, n_modes, output, expr, output_coeff_data, output_input_vars)

# print the coefficient data
print('\t// Output coefficient data')
for coeff_name, coeff_array in output_coeff_data.items():
    print('\tcoeff ' + coeff_name + ' [] = ' + array(coeff_array) + ';')
print()

# print the update equations
print('\t// Output update equations')
for output, vars in output_input_vars.items():
    print('\t*' + output + ' = ', end='')
    update = []
    update.append(const(output)+at_mode())
    for var in vars:
        var_name = local(var) if var not in ext_set else var
        update.append(to(var, output) + at_mode() + '*' + var_name)
    print(' + '.join(update) + ';')

# end function
print('}')