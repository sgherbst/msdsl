#ifndef TYPE_DEFS_H_
#define TYPE_DEFS_H_

#include "ap_int.h"
#include "ap_fixed.h"

#ifndef STIMULUS_LEN
#define STIMULUS_LEN 256
#endif

// Default Datatypes
typedef ap_fixed<25, 12> real;
typedef ap_fixed<25, 12> coeff;
typedef ap_uint<1> bit;

// Signal Specific Datatypes
typedef real local_i_L0_ap;
typedef real local_v_C0_ap;
typedef coeff i_L0_const_ap;
typedef coeff v_C0_const_ap;
typedef coeff output_to_v_C0_ap;
typedef coeff v_C0_to_v_C0_ap;
typedef coeff i_L0_to_i_L0_ap;
typedef coeff input_to_i_L0_ap;
typedef coeff v_C0_to_i_L0_ap;
typedef coeff i_L0_to_v_C0_ap;
typedef coeff i_D0_const_ap;
typedef coeff v_D0_const_ap;
typedef coeff v_C0_to_v_D0_ap;
typedef coeff input_to_v_D0_ap;
typedef coeff i_L0_to_i_D0_ap;
typedef real local_v_D0_ap;
typedef real local_i_D0_ap;
typedef coeff v_out_const_ap;
typedef coeff v_C0_to_v_out_ap;
typedef real input_ap;
typedef real output_ap;
typedef real v_out_ap;

#endif // TYPE_DEFS_H_ not defined
