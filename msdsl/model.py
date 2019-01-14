from msdsl.verilog import VerilogGenerator

class AnalogModel:
    def __init__(self, name='analog_model', inputs=None, outputs=None):
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []

        self.name = name
        self.inputs = inputs
        self.outputs = outputs

    def write(self, filename):
        gen = VerilogGenerator(filename)

        # set timescale
        gen.timescale()
        gen.println()

        # include real number library
        gen.include('real.sv')
        gen.println()

        # determine parameters
        parameters = [f'`DECL_REAL({io})' for io in self.inputs+self.outputs]

        # determine IOs
        ios = ['input wire logic clk', 'input wire logic rst']
        ios.extend([f'`INPUT_REAL({input})' for input in self.inputs])
        ios.extend([f'`OUTPUT_REAL({output})' for output in self.outputs])

        # start module
        gen.start_module(name=self.name, parameters=parameters, ios=ios)

        # main model
        filler = """
// compute the next state as a blend of the input and output
`MUL_CONST_REAL(0.3, in, prod_1);
`MUL_CONST_REAL(0.7, out, prod_2);
`ADD_REAL(prod_1, prod_2, next);

// update the state on every clock edge
`MEM_INTO_REAL(next, out);
        """
        for line in filler.split('\n'):
            gen.println(line)

        gen.end_module()