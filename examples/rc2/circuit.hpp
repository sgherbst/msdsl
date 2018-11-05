#ifndef __CIRCUIT_HPP__
#define __CIRCUIT_HPP__

#include "ap_int.h"
#include "ap_fixed.h"

#define LESS_THAN_ZERO(x) ap_uint<1>(((x) < 0) ? 1 : 0)

// analog inputs
typedef float input_type;

// digital inputs

// analog outputs
