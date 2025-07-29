// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <stdio.h>
#ifndef ASSERT_EQ
#define ASSERT_EQ(a, b)                                                                 \
    do                                                                                  \
    {                                                                                   \
        if ((a) != (b))                                                                 \
        {                                                                               \
            fprintf(stderr, "Test fail: %s - %s:%d", __FUNCTION__, __FILE__, __LINE__); \
            abort();                                                                    \
        }                                                                               \
    } while (false)
#endif // ASSERT_EQ
#ifndef ASSERT_NE
#define ASSERT_NE(a, b)                                                                 \
    do                                                                                  \
    {                                                                                   \
        if ((a) == (b))                                                                 \
        {                                                                               \
            fprintf(stderr, "Test fail: %s - %s:%d", __FUNCTION__, __FILE__, __LINE__); \
            abort();                                                                    \
        }                                                                               \
    } while (false)
#endif // ASSERT_NE

#ifndef ASSERT_FALSE
#define ASSERT_FALSE(a)                                                                 \
    do                                                                                  \
    {                                                                                   \
        if (a)                                                                          \
        {                                                                               \
            fprintf(stderr, "Test fail: %s - %s:%d", __FUNCTION__, __FILE__, __LINE__); \
            abort();                                                                    \
        }                                                                               \
    } while (false)
#endif // ASSERT_FALSE

#ifndef ASSERT_TRUE
#define ASSERT_TRUE(a)                                                                  \
    do                                                                                  \
    {                                                                                   \
        if (!(a))                                                                       \
        {                                                                               \
            fprintf(stderr, "Test fail: %s - %s:%d", __FUNCTION__, __FILE__, __LINE__); \
            abort();                                                                    \
        }                                                                               \
    } while (false)
#endif // ASSERT_TRUE

bool TEST_add_uint32_mod();
bool TEST_multiply_uint_mod();
bool TEST_exponentiate_uint32_mod();
bool TEST_negate_uint_mod();
bool TEST_try_invert_uint_mod32();
bool TEST_get_msb_index();
bool TEST_get_significant_bit_count();
bool TEST_get_significant_bit_count_uint();
bool TEST_divide_uint96_inplace();
bool TEST_left_shift_uint96();
bool TEST_right_shift_uint96();
bool TEST_add_uint32_base();
bool TEST_sub_uint32_base();
bool TEST_xgcd32();
bool TEST_reverse_bits();

bool TEST_add_uint64_mod();
bool TEST_exponentiate_uint64_mod();
bool TEST_divide_uint192_inplace();
bool TEST_left_shift_uint192();
bool TEST_right_shift_uint192();
bool TEST_add_uint64_base();
bool TEST_sub_uint64_base();
bool TEST_montgomery_add();
bool TEST_montgomery_mul();
#endif // SRC_DATA_FORMATS_TEST_MATH_UNITTEST_UNITTEST_H_
