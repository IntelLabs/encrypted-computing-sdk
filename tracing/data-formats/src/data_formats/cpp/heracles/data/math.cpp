// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/data/math.h"
#include <iostream>
#include <stdexcept>
#include <vector>

std::uint32_t heracles::math::reverse_bits(std::uint32_t operand, std::uint32_t bit_count)
{
    uint32_t c[2];
    multiply_uint(operand, operand, c);

    if (bit_count == 0)
        return 0;

    operand = (((operand & uint32_t(0xaaaaaaaaU)) >> 1) | ((operand & uint32_t(0x55555555U)) << 1));
    operand = (((operand & uint32_t(0xccccccccU)) >> 2) | ((operand & uint32_t(0x33333333U)) << 2));
    operand = (((operand & uint32_t(0xf0f0f0f0U)) >> 4) | ((operand & uint32_t(0x0f0f0f0fU)) << 4));
    operand = (((operand & uint32_t(0xff00ff00U)) >> 8) | ((operand & uint32_t(0x00ff00ffU)) << 8));
    return (static_cast<uint32_t>(operand >> 16) | static_cast<uint32_t>(operand << 16)) >>
           (32 - static_cast<size_t>(bit_count));
}

template <>
void heracles::math::multiply_uint<uint32_t>(uint32_t operand1, uint32_t operand2, uint32_t *result)
{
    auto operand1_coeff_right = operand1 & 0x0000FFFFU;
    auto operand2_coeff_right = operand2 & 0x0000FFFFU;

    operand1 >>= 16;
    operand2 >>= 16;
    auto middle1 = operand1 * operand2_coeff_right;
    uint32_t middle;
    auto left = operand1 * operand2 +
                (static_cast<uint32_t>(add_uint(middle1, operand2 * operand1_coeff_right, &middle)) << 16);
    auto right = operand1_coeff_right * operand2_coeff_right;
    auto temp_sum = (right >> 16) + (middle & 0x0000FFFFU);
    result[1] = static_cast<uint32_t>(left + (middle >> 16) + (temp_sum >> 16));
    result[0] = static_cast<uint32_t>((temp_sum << 16) | (right & 0x0000FFFFU));
}

template <>
void heracles::math::multiply_uint<uint64_t>(uint64_t operand1, uint64_t operand2, uint64_t *result)
{
    auto operand1_coeff_right = operand1 & 0x00000000FFFFFFFFUL;
    auto operand2_coeff_right = operand2 & 0x00000000FFFFFFFFUL;

    operand1 >>= 32;
    operand2 >>= 32;
    auto middle1 = operand1 * operand2_coeff_right;
    uint64_t middle;
    auto left = operand1 * operand2 +
                (static_cast<uint64_t>(add_uint(middle1, operand2 * operand1_coeff_right, &middle)) << 32);
    auto right = operand1_coeff_right * operand2_coeff_right;
    auto temp_sum = (right >> 32) + (middle & 0x00000000FFFFFFFFUL);
    result[1] = static_cast<uint64_t>(left + (middle >> 32) + (temp_sum >> 32));
    result[0] = static_cast<uint64_t>((temp_sum << 32) | (right & 0x00000000FFFFFFFFUL));
}

template <>
size_t heracles::math::get_msb_index<uint32_t>(std::uint32_t value)
{
    static const std::uint8_t BitPositionLookup[32] = { 0,  1,  16, 2,  29, 17, 3,  22, 30, 20, 18, 11, 13, 4, 7,  23,
                                                        31, 15, 28, 21, 19, 10, 12, 6,  14, 27, 9,  5,  26, 8, 25, 24 };

    value |= (value >> 1);
    value |= (value >> 2);
    value |= (value >> 4);
    value |= (value >> 8);
    value |= (value >> 16);

    return BitPositionLookup[((value - (value >> 1)) * 0x06EB14F9U) >> 27];
}

template <>
size_t heracles::math::get_msb_index<uint64_t>(std::uint64_t value)
{
    static const std::uint8_t BitPositionLookup[64] = { 63, 0,  58, 1,  59, 47, 53, 2,  60, 39, 48, 27, 54, 33, 42, 3,
                                                        61, 51, 37, 40, 49, 18, 28, 20, 55, 30, 34, 11, 43, 14, 22, 4,
                                                        62, 57, 46, 52, 38, 26, 32, 41, 50, 36, 17, 19, 29, 10, 13, 21,
                                                        56, 45, 25, 31, 35, 16, 9,  12, 44, 24, 15, 8,  23, 7,  6,  5 };
    value |= (value >> 1);
    value |= (value >> 2);
    value |= (value >> 4);
    value |= (value >> 8);
    value |= (value >> 16);
    value |= (value >> 32);

    return BitPositionLookup[((value - (value >> 1)) * 0x07EDD5E59A4E28C2UL) >> 58];
}

std::tuple<uint64_t, int64_t, int64_t> heracles::math::xgcd(uint64_t x, uint64_t y)
{
    int64_t prev_a = 1;
    int64_t a = 0;
    int64_t prev_b = 0;
    int64_t b = 1;

    while (y != 0)
    {
        int64_t q = static_cast<int64_t>(x / y);
        int64_t temp = static_cast<int64_t>(x % y);
        x = y;
        y = static_cast<uint64_t>(temp);

        temp = a;
        a = prev_a - a * q;
        prev_a = temp;

        temp = b;
        b = prev_b - b * q;
        prev_b = temp;
    }
    return std::make_tuple(x, prev_a, prev_b);
}

std::tuple<uint32_t, int32_t, int32_t> heracles::math::xgcd(uint32_t x, uint32_t y)
{
    int32_t prev_a = 1;
    int32_t a = 0;
    int32_t prev_b = 0;
    int32_t b = 1;

    while (y != 0)
    {
        int32_t q = static_cast<int32_t>(x / y);
        int32_t temp = static_cast<int32_t>(x % y);
        x = y;
        y = static_cast<uint32_t>(temp);

        temp = a;
        a = prev_a - a * q;
        prev_a = temp;

        temp = b;
        b = prev_b - b * q;
        prev_b = temp;
    }
    return std::make_tuple(x, prev_a, prev_b);
}
