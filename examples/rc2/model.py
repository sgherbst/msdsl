from msdsl.model import Model

class RC2(Model):
    def __init__(self, r=10e3, r_switch=1e3, c=1e-9, v_init=0, i_init=0, name=None):
        super().__init__(a_in='v_in', d_in='switch_in',  a_out='v_out', 
                a_state={'v_cap': v_init, 'i_ind':i_init}, name=name)



        self.r = r
        self.r_switch = r_switch
        self.r_parallel = 1/(1/self.r+1/self.r_switch)
        self.c = c

        mosfet_modes = self.digital_dependence('switch_in')

        self.v_cap.expr[mosfet_modes[0]] = (self.v_in-self.v_cap)/(self.r*self.c)
        self.v_cap.expr[mosfet_modes[1]] = (self.v_in-self.v_cap)/(self.r_parallel*self.c)
        self.v_out.expr = self.v_cap

def main():
    # create circuit
    rc2 = RC2()

    # emit FPGA model
    rc2.emit('fpga')

if __name__ == '__main__':
    main()
