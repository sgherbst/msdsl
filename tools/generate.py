import argparse

from msdsl.format import load_model
from msdsl.util import Namespace
from msdsl.cpp import *
from msdsl.expr import ModelExpr

def get_io_list(model):
    io_list = []

    for io in model.ios:
        io_type = io.name + '_type'
        if io.isa('output'):
            io_type = ptr(io_type)
        io_list.append((io_type, io.name))

    return sorted(io_list, key=lambda x: x[1].lower())

def make_header(args, model):
    cpp_gen = CppGen(filename=args.hpp)

    # start include guard
    include_guard_var = '__' + args.hpp.upper().replace('.', '_') + '__'
    cpp_gen.start_include_guard(include_guard_var)
    cpp_gen.print()

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    # write typedefs
    cpp_gen.comment('I/O')
    for io in model.ios:
        typedef_name = io.name + '_type'
        cpp_gen.typedef(io.to_hls(), typedef_name)
    cpp_gen.print()

    # declare function prototype
    cpp_gen.comment('function prototype')
    cpp_gen.function_prototype('void', 'circuit', get_io_list(model))
    cpp_gen.print()

    # end include guard
    cpp_gen.end_include_guard(include_guard_var)

def make_source(args, model):
    cpp_gen = CppGen(filename=args.cpp)
    namespace = Namespace()

    # include files
    cpp_gen.include('"ap_int.h"')
    cpp_gen.include('"ap_fixed.h"')
    cpp_gen.print()

    cpp_gen.include('"' + args.hpp + '"')
    cpp_gen.print()

    # start function representing circuit
    cpp_gen.start_function('void', 'circuit', get_io_list(model))

    # declare state variables
    cpp_gen.comment('State variables')
    for state in model.states:
        cpp_gen.static(state.to_hls(), state.name, initial=state.value)
    cpp_gen.print()

    # declare constants
    cpp_gen.comment('Constants')
    for constant in model.constants:
        if constant.value is not None:
            cpp_gen.assign(constant.to_hls() + ' ' + constant.name, str(constant.value))
        else:
            cpp_gen.array(constant.to_hls(), constant.name, constant.array)
    cpp_gen.print()

    # implement the assignment groups
    for assignment_group in model.assignment_groups:
        # do temporary assignments if necessary
        if len(assignment_group) > 1:
            cpp_gen.comment('Assignment group')
            for assignment in assignment_group:
                tmp = namespace.make(prefix='tmp')
                cpp_gen.assign(model.get_by_name(assignment.lhs).to_hls() + ' ' + tmp, assignment.rhs.to_hls())
                assignment.rhs = tmp

        # make assignments
        for assignment in assignment_group:
            lhs = assignment.lhs
            if model.isa(lhs, 'output'):
                lhs = '*' + lhs
            elif model.isa(lhs, 'internal'):
                lhs = model.get_by_name(lhs).to_hls() + ' ' + lhs

            rhs = assignment.rhs
            if isinstance(rhs, ModelExpr):
                rhs = rhs.to_hls()

            cpp_gen.assign(lhs, rhs)

        cpp_gen.print()

    cpp_gen.end_function()

def main():
    parser = argparse.ArgumentParser(description='Generate C++ code from mixed-signal intermediate representation.')
    parser.add_argument('--json', type=str, help='Input JSON file.', default='circuit.json')
    parser.add_argument('--cpp', type=str, help='Output C++ source file.', default='circuit.cpp')
    parser.add_argument('--hpp', type=str, help='Output C++ header file.', default='circuit.hpp')
    parser.add_argument('--use_float', action='store_true', help='Use floating-point numbers (instead of fixed-point)')

    args = parser.parse_args()

    file_text = open(args.json, 'r').read()
    model = load_model(file_text)

    # make the header
    make_header(args=args, model=model)

    # make the source code
    make_source(args=args, model=model)

if __name__ == '__main__':
    main()