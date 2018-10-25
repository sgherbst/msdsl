from msdsl.model import Model

class RC(Model):
    def __init__(self, r=10e3, c=1e-9, v_init=0, name=None):
        super().__init__(a_in='v_in', a_out='v_out', a_state={'v_cap': v_init}, name=name)

        self.r = r
        self.c = c

        self.v_cap.expr = (self.v_in-self.v_cap)/(self.r*self.c)
        self.v_out.expr = self.v_cap

def main():
    # create circuit
    rc = RC()

    # emit FPGA model
    rc.emit('fpga')

if __name__ == '__main__':
    main()