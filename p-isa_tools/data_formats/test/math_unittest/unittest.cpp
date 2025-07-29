// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "unittest.h"
#include <cstdint>
#include <iostream>
#include <tuple>
#include <vector>
#include "heracles/data/math.h"

bool TEST_add_uint32_mod()
{
    std::uint32_t mod;

    mod = 2;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint32_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(1, 0, mod));
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint32_t>(1, 1, mod));

    mod = 10;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint32_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(1, 0, mod));
    ASSERT_EQ(2, heracles::math::add_uint_mod<uint32_t>(1, 1, mod));
    ASSERT_EQ(4, heracles::math::add_uint_mod<uint32_t>(7, 7, mod));
    ASSERT_EQ(3, heracles::math::add_uint_mod<uint32_t>(6, 7, mod));

    mod = 1305843001;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint32_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(1, 0, mod));
    ASSERT_EQ(2, heracles::math::add_uint_mod<uint32_t>(1, 1, mod));
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint32_t>(652921500, 652921501, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint32_t>(652921501, 652921501, mod));
    ASSERT_EQ(1305842999, heracles::math::add_uint_mod<uint32_t>(1305843000, 1305843000, mod));

    return true;
}

bool TEST_multiply_uint_mod()
{
    std::uint32_t mod;

    mod = 2;
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 0U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 1U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(1U, 0U, mod));
    ASSERT_EQ(1, heracles::math::multiply_uint_mod(1U, 1U, mod));

    mod = 10;
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 0U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 1U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(1U, 0U, mod));
    ASSERT_EQ(1, heracles::math::multiply_uint_mod(1U, 1U, mod));
    ASSERT_EQ(9, heracles::math::multiply_uint_mod(7U, 7U, mod));
    ASSERT_EQ(2, heracles::math::multiply_uint_mod(6U, 7U, mod));
    ASSERT_EQ(2, heracles::math::multiply_uint_mod(7U, 6U, mod));

    mod = 1305843001;
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 0U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(0U, 1U, mod));
    ASSERT_EQ(0, heracles::math::multiply_uint_mod(1U, 0U, mod));
    ASSERT_EQ(1, heracles::math::multiply_uint_mod(1U, 1U, mod));
    ASSERT_EQ(326460750, heracles::math::multiply_uint_mod(652921500U, 652921501U, mod));
    ASSERT_EQ(326460750, heracles::math::multiply_uint_mod(652921501U, 652921500U, mod));
    ASSERT_EQ(979382251, heracles::math::multiply_uint_mod(652921501U, 652921501U, mod));
    ASSERT_EQ(1, heracles::math::multiply_uint_mod(1305843000U, 1305843000U, mod));

    return true;
}

bool TEST_exponentiate_uint32_mod()
{
    std::uint32_t mod;

    mod = 5;
    ASSERT_EQ(1, heracles::math::exponentiate_uint_mod(1U, 0U, mod));
    ASSERT_EQ(1, heracles::math::exponentiate_uint_mod(1U, 0xFFFFFFFFU, mod));
    ASSERT_EQ(3, heracles::math::exponentiate_uint_mod(2U, 0xFFFFFFFFU, mod));

    mod = 0x10000000;
    ASSERT_EQ(0, heracles::math::exponentiate_uint_mod(2U, 30U, mod));
    ASSERT_EQ(0, heracles::math::exponentiate_uint_mod(2U, 59U, mod));

    mod = 131313131;
    ASSERT_EQ(26909095, heracles::math::exponentiate_uint_mod(242424242U, 16U, mod));

    return true;
}

bool TEST_negate_uint_mod()
{
    std::uint32_t mod;

    mod = 2;
    ASSERT_EQ(0, heracles::math::negate_uint_mod(0U, mod));
    ASSERT_EQ(1, heracles::math::negate_uint_mod(1U, mod));

    mod = 0xFFFF;
    ASSERT_EQ(0, heracles::math::negate_uint_mod(0U, mod));
    ASSERT_EQ(0xFFFE, heracles::math::negate_uint_mod(1U, mod));
    ASSERT_EQ(1, heracles::math::negate_uint_mod(0xFFFEU, mod));

    mod = 1844674403;
    ASSERT_EQ(0, heracles::math::negate_uint_mod(0U, mod));
    ASSERT_EQ(1844674402, heracles::math::negate_uint_mod(1U, mod));

    return true;
}

bool TEST_try_invert_uint_mod32()
{
    std::uint32_t mod, result;

    mod = 5;
    ASSERT_EQ(false, heracles::math::try_invert_uint_mod(0U, mod, &result));
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(1U, mod, &result));
    ASSERT_EQ(1, result);
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(2U, mod, &result));
    ASSERT_EQ(3, result);
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(3U, mod, &result));
    ASSERT_EQ(2, result);
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(4U, mod, &result));
    ASSERT_EQ(4, result);

    mod = 6;
    ASSERT_EQ(false, heracles::math::try_invert_uint_mod(2U, mod, &result));
    ASSERT_EQ(false, heracles::math::try_invert_uint_mod(3U, mod, &result));
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(5U, mod, &result));
    ASSERT_EQ(5, result);

    mod = 1351315121;
    ASSERT_EQ(true, heracles::math::try_invert_uint_mod(331975426U, mod, &result));
    ASSERT_EQ(1052541512, result);

    return true;
}

bool TEST_get_significant_bit_count_uint()
{
    std::vector<std::uint32_t> val(2, 0);

    val[0] = 0;
    val[1] = 0;
    ASSERT_EQ(0, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 1;
    val[1] = 0;
    ASSERT_EQ(1, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 2;
    val[1] = 0;
    ASSERT_EQ(2, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 3;
    val[1] = 0;
    ASSERT_EQ(2, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 29;
    val[1] = 0;
    ASSERT_EQ(5, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 4;
    val[1] = 0;
    ASSERT_EQ(3, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0xFFFFFFFF;
    val[1] = 0;
    ASSERT_EQ(32, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0;
    val[1] = 1;
    ASSERT_EQ(33, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0xFFFFFFFF;
    val[1] = 1;
    ASSERT_EQ(33, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0xFFFFFFFF;
    val[1] = 0x70000000;
    ASSERT_EQ(63, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0xFFFFFFFF;
    val[1] = 0x80000000;
    ASSERT_EQ(64, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    val[0] = 0xFFFFFFFF;
    val[1] = 0xFFFFFFFF;
    ASSERT_EQ(64, heracles::math::get_significant_bit_count_uint(val.data(), 2));

    std::vector<std::uint64_t> val64(2, 0);

    val64[0] = 0;
    val64[1] = 0;
    ASSERT_EQ(0, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 1;
    val64[1] = 0;
    ASSERT_EQ(1, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 2;
    val64[1] = 0;
    ASSERT_EQ(2, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 3;
    val64[1] = 0;
    ASSERT_EQ(2, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 29;
    val64[1] = 0;
    ASSERT_EQ(5, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 4;
    val64[1] = 0;
    ASSERT_EQ(3, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0xFFFFFFFF;
    val64[1] = 0;
    ASSERT_EQ(32, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0;
    val64[1] = 1;
    ASSERT_EQ(65, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0xFFFFFFFF;
    val64[1] = 1;
    ASSERT_EQ(65, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0xFFFFFFFFFFFFFFFF;
    val64[1] = 0x7000000000000000;
    ASSERT_EQ(127, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0xFFFFFFFFFFFFFFFF;
    val64[1] = 0x8000000000000000;
    ASSERT_EQ(128, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    val64[0] = 0xFFFFFFFFFFFFFFFF;
    val64[1] = 0xFFFFFFFFFFFFFFFF;
    ASSERT_EQ(128, heracles::math::get_significant_bit_count_uint(val64.data(), 2));

    return true;
}

bool TEST_divide_uint96_inplace()
{
    std::vector<std::uint32_t> input(3, 0);
    std::vector<std::uint32_t> quotient(3, 0);

    input[0] = 0;
    input[1] = 0;
    input[2] = 0;
    heracles::math::divide_uint3_inplace(input.data(), 1U, quotient.data());
    ASSERT_EQ(0, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(0, quotient[0]);
    ASSERT_EQ(0, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    input[0] = 1;
    input[1] = 0;
    input[2] = 0;
    heracles::math::divide_uint3_inplace(input.data(), 1U, quotient.data());
    ASSERT_EQ(0, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(1, quotient[0]);
    ASSERT_EQ(0, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    input[0] = 0x10101010U;
    input[1] = 0x2B2B2B2BU;
    input[2] = 0xF1F1F1F1U;
    heracles::math::divide_uint3_inplace(input.data(), 0x1000U, quotient.data());
    ASSERT_EQ(0x10, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(0xB2B10101, quotient[0]);
    ASSERT_EQ(0x1F12B2B2, quotient[1]);
    ASSERT_EQ(0xF1F1F, quotient[2]);

    input[0] = 12121212;
    input[1] = 34343434;
    input[2] = 56565656;
    heracles::math::divide_uint3_inplace(input.data(), 78787878U, quotient.data());
    ASSERT_EQ(18181818, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(991146299, quotient[0]);
    ASSERT_EQ(3083566264, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    return true;
}

bool TEST_left_shift_uint96()
{
    std::vector<std::uint32_t> a(3, 0);
    std::vector<std::uint32_t> b(3, 0xFFFFFFFF);

    heracles::math::left_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    std::fill_n(b.data(), b.size(), 0xFFFFFFFF);
    heracles::math::left_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::left_shift_uint3(a.data(), 10, a.data());
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0, a[1]);
    ASSERT_EQ(0, a[2]);

    a[0] = 0x55555555;
    a[1] = 0xAAAAAAAA;
    a[2] = 0xCDCDCDCD;
    heracles::math::left_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0x55555555, b[0]);
    ASSERT_EQ(0xAAAAAAAA, b[1]);
    ASSERT_EQ(0xCDCDCDCD, b[2]);
    heracles::math::left_shift_uint3(a.data(), 0, a.data());
    ASSERT_EQ(0x55555555, a[0]);
    ASSERT_EQ(0xAAAAAAAA, a[1]);
    ASSERT_EQ(0xCDCDCDCD, a[2]);
    heracles::math::left_shift_uint3(a.data(), 1, b.data());
    ASSERT_EQ(0xAAAAAAAA, b[0]);
    ASSERT_EQ(0x55555554, b[1]);
    ASSERT_EQ(0x9B9B9B9B, b[2]);
    heracles::math::left_shift_uint3(a.data(), 2, b.data());
    ASSERT_EQ(0x55555554, b[0]);
    ASSERT_EQ(0xAAAAAAA9, b[1]);
    ASSERT_EQ(0x37373736, b[2]);
    heracles::math::left_shift_uint3(a.data(), 32, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0x55555555, b[1]);
    ASSERT_EQ(0xAAAAAAAA, b[2]);
    heracles::math::left_shift_uint3(a.data(), 33, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0xAAAAAAAA, b[1]);
    ASSERT_EQ(0x55555554, b[2]);
    heracles::math::left_shift_uint3(a.data(), 95, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0x80000000, b[2]);

    heracles::math::left_shift_uint3(a.data(), 2, a.data());
    ASSERT_EQ(0x55555554, a[0]);
    ASSERT_EQ(0xAAAAAAA9, a[1]);
    ASSERT_EQ(0x37373736, a[2]);

    heracles::math::left_shift_uint3(a.data(), 32, a.data());
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0x55555554, a[1]);
    ASSERT_EQ(0xAAAAAAA9, a[2]);

    return true;
}

bool TEST_right_shift_uint96()
{
    std::vector<std::uint32_t> a(3, 0);
    std::vector<std::uint32_t> b(3, 0xFFFFFFFF);

    heracles::math::right_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    std::fill_n(b.data(), b.size(), 0xFFFFFFFF);
    heracles::math::right_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    a[0] = 0x55555555;
    a[1] = 0xAAAAAAAA;
    a[2] = 0xCDCDCDCD;
    heracles::math::right_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0x55555555, b[0]);
    ASSERT_EQ(0xAAAAAAAA, b[1]);
    ASSERT_EQ(0xCDCDCDCD, b[2]);
    heracles::math::right_shift_uint3(a.data(), 0, a.data());
    ASSERT_EQ(0x55555555, a[0]);
    ASSERT_EQ(0xAAAAAAAA, a[1]);
    ASSERT_EQ(0xCDCDCDCD, a[2]);
    heracles::math::right_shift_uint3(a.data(), 1, b.data());
    ASSERT_EQ(0x2AAAAAAA, b[0]);
    ASSERT_EQ(0xD5555555, b[1]);
    ASSERT_EQ(0x66E6E6E6, b[2]);
    heracles::math::right_shift_uint3(a.data(), 2, b.data());
    ASSERT_EQ(0x95555555, b[0]);
    ASSERT_EQ(0x6AAAAAAA, b[1]);
    ASSERT_EQ(0x33737373, b[2]);
    heracles::math::right_shift_uint3(a.data(), 32, b.data());
    ASSERT_EQ(0xAAAAAAAA, b[0]);
    ASSERT_EQ(0xCDCDCDCD, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 33, b.data());
    ASSERT_EQ(0xD5555555, b[0]);
    ASSERT_EQ(0x66E6E6E6, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 95, b.data());
    ASSERT_EQ(1, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    heracles::math::right_shift_uint3(a.data(), 2, a.data());
    ASSERT_EQ(0x95555555, a[0]);
    ASSERT_EQ(0x6AAAAAAA, a[1]);
    ASSERT_EQ(0x33737373, a[2]);

    heracles::math::right_shift_uint3(a.data(), 32, a.data());
    ASSERT_EQ(0x6AAAAAAA, a[0]);
    ASSERT_EQ(0x33737373, a[1]);
    ASSERT_EQ(0, a[2]);

    return true;
}

bool TEST_add_uint32_base()
{
    std::vector<std::uint32_t> a(2, 0);
    std::vector<std::uint32_t> b(2, 0);
    std::vector<std::uint32_t> c(2);

    c[0] = 0xFFFFFFFF;
    c[1] = 0xFFFFFFFF;

    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFE;
    a[1] = 0xFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0xFFFFFFFF;
    b[1] = 0xFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFE, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0xFFFFFFFE, a[0]);
    ASSERT_EQ(0xFFFFFFFF, a[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(1, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 5;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(6, c[1]);

    return true;
}

bool TEST_sub_uint32_base()
{
    std::vector<std::uint32_t> a(2, 0);
    std::vector<std::uint32_t> b(2, 0);
    std::vector<std::uint32_t> c(2);

    c[0] = 0xFFFFFFFF;
    c[1] = 0xFFFFFFFF;

    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFE, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0;
    a[1] = 0;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0xFFFFFFFF, a[0]);
    ASSERT_EQ(0xFFFFFFFF, a[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0xFFFFFFFF;
    b[1] = 0xFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0, a[1]);

    a[0] = 0xFFFFFFFE;
    a[1] = 0xFFFFFFFF;
    b[0] = 0xFFFFFFFF;
    b[1] = 0xFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0;
    a[1] = 1;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0, c[1]);

    return true;
}

bool TEST_xgcd32()
{
    std::tuple<std::uint32_t, int32_t, int32_t> result;

    result = heracles::math::xgcd(7U, 7U);
    ASSERT_EQ(result, std::make_tuple<>(7, 0, 1));
    result = heracles::math::xgcd(2U, 2U);
    ASSERT_EQ(result, std::make_tuple<>(2, 0, 1));

    result = heracles::math::xgcd(1U, 1U);
    ASSERT_EQ(result, std::make_tuple<>(1, 0, 1));
    result = heracles::math::xgcd(1U, 2U);
    ASSERT_EQ(result, std::make_tuple<>(1, 1, 0));
    result = heracles::math::xgcd(5U, 6U);
    ASSERT_EQ(result, std::make_tuple<>(1, -1, 1));
    result = heracles::math::xgcd(13U, 19U);
    ASSERT_EQ(result, std::make_tuple<>(1, 3, -2));
    result = heracles::math::xgcd(14U, 21U);
    ASSERT_EQ(result, std::make_tuple<>(7, -1, 1));

    result = heracles::math::xgcd(2U, 1U);
    ASSERT_EQ(result, std::make_tuple<>(1, 0, 1));
    result = heracles::math::xgcd(6U, 5U);
    ASSERT_EQ(result, std::make_tuple<>(1, 1, -1));
    result = heracles::math::xgcd(19U, 13U);
    ASSERT_EQ(result, std::make_tuple<>(1, -2, 3));
    result = heracles::math::xgcd(21U, 14U);
    ASSERT_EQ(result, std::make_tuple<>(7, 1, -1));

    return true;
}

bool TEST_reverse_bits()
{
    ASSERT_EQ(0, heracles::math::reverse_bits(0));
    ASSERT_EQ(0x80000000, heracles::math::reverse_bits(1));
    ASSERT_EQ(0x40000000, heracles::math::reverse_bits(2));
    ASSERT_EQ(0xC0000000, heracles::math::reverse_bits(3));
    ASSERT_EQ(0x00010000, heracles::math::reverse_bits(0x00008000));
    ASSERT_EQ(0xFFFF0000, heracles::math::reverse_bits(0x0000FFFF));
    ASSERT_EQ(0x0000FFFF, heracles::math::reverse_bits(0xFFFF0000));
    ASSERT_EQ(0x00008000, heracles::math::reverse_bits(0x00010000));

    ASSERT_EQ(0, heracles::math::reverse_bits(0xFFFFFFFF, 0));

    ASSERT_EQ(0, heracles::math::reverse_bits(0, 32));
    ASSERT_EQ(0x80000000, heracles::math::reverse_bits(1, 32));
    ASSERT_EQ(0x40000000, heracles::math::reverse_bits(2, 32));
    ASSERT_EQ(0xC0000000, heracles::math::reverse_bits(3, 32));
    ASSERT_EQ(0x00010000, heracles::math::reverse_bits(0x00008000, 32));
    ASSERT_EQ(0xFFFF0000, heracles::math::reverse_bits(0x0000FFFF, 32));
    ASSERT_EQ(0x0000FFFF, heracles::math::reverse_bits(0xFFFF0000, 32));
    ASSERT_EQ(0x00008000, heracles::math::reverse_bits(0x00010000, 32));

    ASSERT_EQ(0, heracles::math::reverse_bits(0, 16));
    ASSERT_EQ(0x00008000, heracles::math::reverse_bits(1, 16));
    ASSERT_EQ(0x00004000, heracles::math::reverse_bits(2, 16));
    ASSERT_EQ(0x0000C000, heracles::math::reverse_bits(3, 16));
    ASSERT_EQ(0x00000001, heracles::math::reverse_bits(0x00008000, 16));
    ASSERT_EQ(0x0000FFFF, heracles::math::reverse_bits(0x0000FFFF, 16));
    ASSERT_EQ(0x00000000, heracles::math::reverse_bits(0xFFFF0000, 16));
    ASSERT_EQ(0x00000000, heracles::math::reverse_bits(0x00010000, 16));
    ASSERT_EQ(3, heracles::math::reverse_bits(0x0000C000, 16));
    ASSERT_EQ(2, heracles::math::reverse_bits(0x00004000, 16));
    ASSERT_EQ(1, heracles::math::reverse_bits(0x00008000, 16));
    ASSERT_EQ(0x0000FFFF, heracles::math::reverse_bits(0xFFFFFFFF, 16));

    return true;
}

bool TEST_add_uint64_mod()
{
    std::uint64_t mod;

    mod = 2;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint64_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(1, 0, mod));
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint64_t>(1, 1, mod));

    mod = 10;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint64_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(1, 0, mod));
    ASSERT_EQ(2, heracles::math::add_uint_mod<uint64_t>(1, 1, mod));
    ASSERT_EQ(4, heracles::math::add_uint_mod<uint64_t>(7, 7, mod));
    ASSERT_EQ(3, heracles::math::add_uint_mod<uint64_t>(6, 7, mod));

    mod = 1305843001;
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint64_t>(0, 0, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(0, 1, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(1, 0, mod));
    ASSERT_EQ(2, heracles::math::add_uint_mod<uint64_t>(1, 1, mod));
    ASSERT_EQ(0, heracles::math::add_uint_mod<uint64_t>(652921500, 652921501, mod));
    ASSERT_EQ(1, heracles::math::add_uint_mod<uint64_t>(652921501, 652921501, mod));
    ASSERT_EQ(1305842999, heracles::math::add_uint_mod<uint64_t>(1305843000, 1305843000, mod));

    return true;
}

bool TEST_exponentiate_uint64_mod()
{
    std::uint64_t mod;

    mod = 5;
    ASSERT_EQ(1, heracles::math::exponentiate_uint_mod(1UL, 0UL, mod));
    ASSERT_EQ(1, heracles::math::exponentiate_uint_mod(1UL, 0xFFFFFFFFFFFFFFFFUL, mod));
    ASSERT_EQ(3, heracles::math::exponentiate_uint_mod(2UL, 0xFFFFFFFFFFFFFFFFUL, mod));

    mod = 0x1000000000000000ULL;
    ASSERT_EQ(0, heracles::math::exponentiate_uint_mod(2UL, 60UL, mod));
    ASSERT_EQ(0x800000000000000ULL, heracles::math::exponentiate_uint_mod(2UL, 59UL, mod));

    mod = 131313131313;
    ASSERT_EQ(39418477653ULL, heracles::math::exponentiate_uint_mod(2424242424UL, 16UL, mod));

    return true;
}

bool TEST_get_msb_index()
{
    ASSERT_EQ(0, heracles::math::get_msb_index(1U));
    ASSERT_EQ(1, heracles::math::get_msb_index(2U));
    ASSERT_EQ(1, heracles::math::get_msb_index(3U));
    ASSERT_EQ(2, heracles::math::get_msb_index(4U));
    ASSERT_EQ(4, heracles::math::get_msb_index(16U));
    ASSERT_EQ(15, heracles::math::get_msb_index(0xFFFFU));
    ASSERT_EQ(15, heracles::math::get_msb_index(0xFFFFUL));
    ASSERT_EQ(16, heracles::math::get_msb_index(0x10000U));
    ASSERT_EQ(16, heracles::math::get_msb_index(0x10000UL));
    ASSERT_EQ(31, heracles::math::get_msb_index(0xFFFFFFFFU));
    ASSERT_EQ(31, heracles::math::get_msb_index(0xFFFFFFFFUL));
    ASSERT_EQ(32, heracles::math::get_msb_index(0x100000000UL));
    ASSERT_EQ(63, heracles::math::get_msb_index(0xFFFFFFFFFFFFFFFFUL));

    return true;
}

bool TEST_get_significant_bit_count()
{
    ASSERT_EQ(0, heracles::math::get_significant_bit_count(0U));
    ASSERT_EQ(1, heracles::math::get_significant_bit_count(1U));
    ASSERT_EQ(2, heracles::math::get_significant_bit_count(2U));
    ASSERT_EQ(2, heracles::math::get_significant_bit_count(3U));
    ASSERT_EQ(3, heracles::math::get_significant_bit_count(4U));
    ASSERT_EQ(3, heracles::math::get_significant_bit_count(5U));
    ASSERT_EQ(3, heracles::math::get_significant_bit_count(6U));
    ASSERT_EQ(3, heracles::math::get_significant_bit_count(7U));
    ASSERT_EQ(4, heracles::math::get_significant_bit_count(8U));
    ASSERT_EQ(31, heracles::math::get_significant_bit_count(0x70000000U));
    ASSERT_EQ(31, heracles::math::get_significant_bit_count(0x7FFFFFFFU));
    ASSERT_EQ(32, heracles::math::get_significant_bit_count(0x80000000U));
    ASSERT_EQ(32, heracles::math::get_significant_bit_count(0xFFFFFFFFU));

    return true;
}

bool TEST_divide_uint192_inplace()
{
    std::vector<std::uint64_t> input(3, 0);
    std::vector<std::uint64_t> quotient(3, 0);

    input[0] = 0;
    input[1] = 0;
    input[2] = 0;
    heracles::math::divide_uint3_inplace(input.data(), 1UL, quotient.data());
    ASSERT_EQ(0, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(0, quotient[0]);
    ASSERT_EQ(0, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    input[0] = 1;
    input[1] = 0;
    input[2] = 0;
    heracles::math::divide_uint3_inplace(input.data(), 1UL, quotient.data());
    ASSERT_EQ(0, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(1, quotient[0]);
    ASSERT_EQ(0, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    input[0] = 0x10101010U;
    input[1] = 0x2B2B2B2BU;
    input[2] = 0xF1F1F1F1U;
    heracles::math::divide_uint3_inplace(input.data(), 0x1000UL, quotient.data());
    ASSERT_EQ(0x10, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(0xB2B0000000010101ULL, quotient[0]);
    ASSERT_EQ(0x1F1000000002B2B2ULL, quotient[1]);
    ASSERT_EQ(0xF1F1FULL, quotient[2]);

    input[0] = 1212121212121212ULL;
    input[1] = 3434343434343434ULL;
    input[2] = 5656565656565656ULL;
    heracles::math::divide_uint3_inplace(input.data(), 7878787878787878UL, quotient.data());
    ASSERT_EQ(7272727272727272ULL, input[0]);
    ASSERT_EQ(0, input[1]);
    ASSERT_EQ(0, input[2]);
    ASSERT_EQ(17027763760347278414ULL, quotient[0]);
    ASSERT_EQ(13243816258047883211ULL, quotient[1]);
    ASSERT_EQ(0, quotient[2]);

    return true;
}

bool TEST_left_shift_uint192()
{
    std::vector<std::uint64_t> a(3, 0);
    std::vector<std::uint64_t> b(3, 0xFFFFFFFFFFFFFFFF);

    heracles::math::left_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    std::fill_n(b.data(), b.size(), 0xFFFFFFFFFFFFFFFF);
    heracles::math::left_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::left_shift_uint3(a.data(), 10, a.data());
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0, a[1]);
    ASSERT_EQ(0, a[2]);

    a[0] = 0x5555555555555555;
    a[1] = 0xAAAAAAAAAAAAAAAA;
    a[2] = 0xCDCDCDCDCDCDCDCD;
    heracles::math::left_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0x5555555555555555, b[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[1]);
    ASSERT_EQ(0xCDCDCDCDCDCDCDCD, b[2]);
    heracles::math::left_shift_uint3(a.data(), 0, a.data());
    ASSERT_EQ(0x5555555555555555, a[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, a[1]);
    ASSERT_EQ(0xCDCDCDCDCDCDCDCD, a[2]);
    heracles::math::left_shift_uint3(a.data(), 1, b.data());
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[0]);
    ASSERT_EQ(0x5555555555555554, b[1]);
    ASSERT_EQ(0x9B9B9B9B9B9B9B9B, b[2]);
    heracles::math::left_shift_uint3(a.data(), 2, b.data());
    ASSERT_EQ(0x5555555555555554, b[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAA9, b[1]);
    ASSERT_EQ(0x3737373737373736, b[2]);
    heracles::math::left_shift_uint3(a.data(), 64, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0x5555555555555555, b[1]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[2]);
    heracles::math::left_shift_uint3(a.data(), 65, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[1]);
    ASSERT_EQ(0x5555555555555554, b[2]);
    heracles::math::left_shift_uint3(a.data(), 191, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0x8000000000000000, b[2]);

    heracles::math::left_shift_uint3(a.data(), 2, a.data());
    ASSERT_EQ(0x5555555555555554, a[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAA9, a[1]);
    ASSERT_EQ(0x3737373737373736, a[2]);

    heracles::math::left_shift_uint3(a.data(), 64, a.data());
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0x5555555555555554, a[1]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAA9, a[2]);

    return true;
}

bool TEST_right_shift_uint192()
{
    std::vector<std::uint64_t> a(3, 0);
    std::vector<std::uint64_t> b(3, 0xFFFFFFFFFFFFFFFF);

    heracles::math::right_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    std::fill_n(b.data(), b.size(), 0xFFFFFFFFFFFFFFFF);
    heracles::math::right_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 10, b.data());
    ASSERT_EQ(0, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    a[0] = 0x5555555555555555;
    a[1] = 0xAAAAAAAAAAAAAAAA;
    a[2] = 0xCDCDCDCDCDCDCDCD;
    heracles::math::right_shift_uint3(a.data(), 0, b.data());
    ASSERT_EQ(0x5555555555555555, b[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[1]);
    ASSERT_EQ(0xCDCDCDCDCDCDCDCD, b[2]);
    heracles::math::right_shift_uint3(a.data(), 0, a.data());
    ASSERT_EQ(0x5555555555555555, a[0]);
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, a[1]);
    ASSERT_EQ(0xCDCDCDCDCDCDCDCD, a[2]);
    heracles::math::right_shift_uint3(a.data(), 1, b.data());
    ASSERT_EQ(0x2AAAAAAAAAAAAAAA, b[0]);
    ASSERT_EQ(0xD555555555555555, b[1]);
    ASSERT_EQ(0x66E6E6E6E6E6E6E6, b[2]);
    heracles::math::right_shift_uint3(a.data(), 2, b.data());
    ASSERT_EQ(0x9555555555555555, b[0]);
    ASSERT_EQ(0x6AAAAAAAAAAAAAAA, b[1]);
    ASSERT_EQ(0x3373737373737373, b[2]);
    heracles::math::right_shift_uint3(a.data(), 64, b.data());
    ASSERT_EQ(0xAAAAAAAAAAAAAAAA, b[0]);
    ASSERT_EQ(0xCDCDCDCDCDCDCDCD, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 65, b.data());
    ASSERT_EQ(0xD555555555555555, b[0]);
    ASSERT_EQ(0x66E6E6E6E6E6E6E6, b[1]);
    ASSERT_EQ(0, b[2]);
    heracles::math::right_shift_uint3(a.data(), 191, b.data());
    ASSERT_EQ(1, b[0]);
    ASSERT_EQ(0, b[1]);
    ASSERT_EQ(0, b[2]);

    heracles::math::right_shift_uint3(a.data(), 2, a.data());
    ASSERT_EQ(0x9555555555555555, a[0]);
    ASSERT_EQ(0x6AAAAAAAAAAAAAAA, a[1]);
    ASSERT_EQ(0x3373737373737373, a[2]);

    heracles::math::right_shift_uint3(a.data(), 64, a.data());
    ASSERT_EQ(0x6AAAAAAAAAAAAAAA, a[0]);
    ASSERT_EQ(0x3373737373737373, a[1]);
    ASSERT_EQ(0, a[2]);

    return true;
}

bool TEST_add_uint64_base()
{
    std::vector<std::uint64_t> a(2, 0);
    std::vector<std::uint64_t> b(2, 0);
    std::vector<std::uint64_t> c(2);

    c[0] = 0xFFFFFFFF;
    c[1] = 0xFFFFFFFF;

    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFE;
    a[1] = 0xFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFFFFFFFFFF;
    a[1] = 0xFFFFFFFFFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0xFFFFFFFFFFFFFFFF);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFFFFFFFFFF;
    a[1] = 0xFFFFFFFFFFFFFFFF;
    b[0] = 0xFFFFFFFFFFFFFFFF;
    b[1] = 0xFFFFFFFFFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFE, c[0]);
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[1]);
    ASSERT_NE(0, heracles::math::add_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFE, a[0]);
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, a[1]);

    a[0] = 0xFFFFFFFFFFFFFFFF;
    a[1] = 0;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(1, c[1]);

    a[0] = 0xFFFFFFFFFFFFFFFF;
    a[1] = 5;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::add_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(6, c[1]);

    return true;
}

bool TEST_sub_uint64_base()
{
    std::vector<std::uint64_t> a(2, 0);
    std::vector<std::uint64_t> b(2, 0);
    std::vector<std::uint64_t> c(2);

    c[0] = 0xFFFFFFFF;
    c[1] = 0xFFFFFFFF;

    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 0;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0xFFFFFFFF;
    a[1] = 0xFFFFFFFF;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFE, c[0]);
    ASSERT_EQ(0xFFFFFFFF, c[1]);

    a[0] = 0;
    a[1] = 0;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[1]);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, a[0]);
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, a[1]);

    a[0] = 0xFFFFFFFFFFFFFFFF;
    a[1] = 0xFFFFFFFFFFFFFFFF;
    b[0] = 0xFFFFFFFFFFFFFFFF;
    b[1] = 0xFFFFFFFFFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0, c[0]);
    ASSERT_EQ(0, c[1]);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, a.data()));
    ASSERT_EQ(0, a[0]);
    ASSERT_EQ(0, a[1]);

    a[0] = 0xFFFFFFFFFFFFFFFE;
    a[1] = 0xFFFFFFFFFFFFFFFF;
    b[0] = 0xFFFFFFFFFFFFFFFF;
    b[1] = 0xFFFFFFFFFFFFFFFF;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_NE(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[0]);
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[1]);

    a[0] = 0;
    a[1] = 1;
    b[0] = 1;
    b[1] = 0;
    std::fill_n(c.data(), c.size(), 0);
    ASSERT_EQ(0, heracles::math::sub_uint_base(a.data(), b.data(), 2, c.data()));
    ASSERT_EQ(0xFFFFFFFFFFFFFFFF, c[0]);
    ASSERT_EQ(0, c[1]);

    return true;
}

bool TEST_montgomery_add()
{
    ASSERT_EQ(11661950U, heracles::math::montgomeryAdd(177890559U, 470380160U, 536608769U));
    ASSERT_EQ(330474188U, heracles::math::montgomeryAdd(192697207U, 137776981U, 536608769U));
    ASSERT_EQ(111700460U, heracles::math::montgomeryAdd(72857859U, 38842601U, 536215553U));
    ASSERT_EQ(301757272U, heracles::math::montgomeryAdd(482904845U, 355067980U, 536215553U));
    ASSERT_EQ(149531932U, heracles::math::montgomeryAdd(83952415U, 65579517U, 1070727169U));
    ASSERT_EQ(176142121U, heracles::math::montgomeryAdd(441592427U, 805276863U, 1070727169U));

    return true;
}

bool TEST_montgomery_mul()
{
    ASSERT_EQ(514071123U, heracles::math::montgomeryMul(166645782U, 378454820U, 1070727169U));
    ASSERT_EQ(930227960U, heracles::math::montgomeryMul(45847266U, 378454820U, 1070727169U));
    ASSERT_EQ(313946907U, heracles::math::montgomeryMul(257508513U, 63724800U, 378470401U));
    ASSERT_EQ(256679068U, heracles::math::montgomeryMul(94982773U, 100100078U, 378470401U));
    ASSERT_EQ(183766988U, heracles::math::montgomeryMul(104720473U, 242438106U, 381616129U));
    ASSERT_EQ(149148360U, heracles::math::montgomeryMul(158503089U, 242438106U, 381616129U));

    return true;
}
