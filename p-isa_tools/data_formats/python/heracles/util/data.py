# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright (C) 2024 Intel Corporation

import heracles.proto.data_pb2 as hpd


# - montgomery transform
montgomery_R_bits = 32
montgomery_R = 1 << montgomery_R_bits


def convert_to_montgomery(num: int, modulus: int) -> int:
    return (num << montgomery_R_bits) % modulus


# - bit-reversal
def poly_bit_reverse_inplace(a: hpd.RNSPolynomial):
    a_in = hpd.RNSPolynomial()
    a_in.CopyFrom(a)
    n = len(a.coeffs)
    j = 0
    for i in range(1, n):
        b = n >> 1
        while j >= b:
            j -= b
            b >>= 1
        j += b
        if j > i:
            a.coeffs[i], a.coeffs[j] = a_in.coeffs[j], a_in.coeffs[i]
