// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "math_unittest/unittest.h"

int main(int /*argc*/, const char * /*argv*/[])
{
    TEST_add_uint32_mod();
    TEST_multiply_uint_mod();
    TEST_exponentiate_uint32_mod();
    TEST_negate_uint_mod();
    TEST_try_invert_uint_mod32();
    TEST_get_msb_index();
    TEST_get_significant_bit_count();
    TEST_get_significant_bit_count_uint();
    TEST_divide_uint96_inplace();
    TEST_left_shift_uint96();
    TEST_right_shift_uint96();
    TEST_add_uint32_base();
    TEST_sub_uint32_base();
    TEST_xgcd32();
    TEST_reverse_bits();

    TEST_add_uint64_mod();
    TEST_exponentiate_uint64_mod();
    TEST_divide_uint192_inplace();
    TEST_left_shift_uint192();
    TEST_right_shift_uint192();
    TEST_add_uint64_base();
    TEST_sub_uint64_base();
}
