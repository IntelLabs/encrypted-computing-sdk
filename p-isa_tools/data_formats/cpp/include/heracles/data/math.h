// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

namespace heracles::math
{
template <typename T, typename...>
struct isUInt : std::conditional<
                    std::is_integral<T>::value && std::is_unsigned<T>::value &&
                        ((sizeof(T) == sizeof(std::uint64_t)) || (sizeof(T) == sizeof(std::uint32_t))),
                    std::true_type, std::false_type>::type
{};
template <typename T, typename...>
constexpr bool is_uint_v = isUInt<T>::value;

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline T add_uint_mod(const T operand1, const T operand2, const T modulus)
{
    T res = operand1 + operand2;
    return res >= modulus ? res - modulus : res;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline T negate_uint_mod(const T operand, const T modulus)
{
    T non_zero = static_cast<T>(operand != 0);
    return (modulus - operand) & static_cast<T>(-non_zero);
}

template <typename T>
inline void multiply_uint(T operand1, T operand2, T *result)
{
    throw std::logic_error("undefined behavior");
}

template <>
void multiply_uint<uint32_t>(uint32_t operand1, uint32_t operand2, uint32_t *result);

template <>
void multiply_uint<uint64_t>(uint64_t operand1, uint64_t operand2, uint64_t *result);

template <typename T>
inline size_t get_msb_index(T value)
{
    throw std::logic_error("undefined behavior");
}

template <>
size_t get_msb_index<uint32_t>(uint32_t value);
template <>
size_t get_msb_index<uint64_t>(uint64_t value);

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline int get_significant_bit_count(T value)
{
    if (value == 0)
        return 0;
    return static_cast<int>(get_msb_index(value) + 1);
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline int get_significant_bit_count_uint(const T *value, size_t uint_count)
{
    const size_t Tbitsz = sizeof(T) * 8;
    value += uint_count - 1;
    while (*value == 0 && uint_count > 1)
    {
        uint_count--;
        value--;
    }
    return static_cast<int>(uint_count - 1) * Tbitsz + get_significant_bit_count(*value);
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline void right_shift_uint3(const T *operand, int shift_amount, T *result)
{
    const size_t Tbitsz = sizeof(T) * 8;
    const size_t shift_amount_sz = static_cast<size_t>(shift_amount);
    if (shift_amount_sz & (Tbitsz * 2))
    {
        result[0] = operand[2];
        result[1] = 0;
        result[2] = 0;
    }
    else if (shift_amount_sz & Tbitsz)
    {
        result[0] = operand[1];
        result[1] = operand[2];
        result[2] = 0;
    }
    else
    {
        result[0] = operand[0];
        result[1] = operand[1];
        result[2] = operand[2];
    }

    size_t bit_shift_amount = shift_amount_sz & (Tbitsz - 1);
    if (bit_shift_amount)
    {
        size_t neg_bit_shift_amount = Tbitsz - bit_shift_amount;
        result[0] = (result[0] >> bit_shift_amount) | (result[1] << neg_bit_shift_amount);
        result[1] = (result[1] >> bit_shift_amount) | (result[2] << neg_bit_shift_amount);
        result[2] = result[2] >> bit_shift_amount;
    }
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline void left_shift_uint3(const T *operand, int shift_amount, T *result)
{
    const size_t Tbitsz = sizeof(T) * 8;
    const size_t shift_amount_sz = static_cast<size_t>(shift_amount);
    if (shift_amount_sz & (Tbitsz * 2))
    {
        result[2] = operand[0];
        result[1] = 0;
        result[0] = 0;
    }
    else if (shift_amount_sz & Tbitsz)
    {
        result[2] = operand[1];
        result[1] = operand[0];
        result[0] = 0;
    }
    else
    {
        result[2] = operand[2];
        result[1] = operand[1];
        result[0] = operand[0];
    }

    size_t bit_shift_amount = shift_amount_sz & (Tbitsz - 1);
    if (bit_shift_amount)
    {
        size_t neg_bit_shift_amount = Tbitsz - bit_shift_amount;
        result[2] = (result[2] << bit_shift_amount) | (result[1] >> neg_bit_shift_amount);
        result[1] = (result[1] << bit_shift_amount) | (result[0] >> neg_bit_shift_amount);
        result[0] = result[0] << bit_shift_amount;
    }
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char add_uint(T operand1, T operand2, T *result)
{
    *result = operand1 + operand2;
    return *result < operand1;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char add_uint(T operand1, T operand2, unsigned char carry, T *result)
{
    operand1 += operand2;
    *result = operand1 + carry;
    return (operand1 < operand2) || (~operand1 < carry);
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char add_uint_base(const T *operand1, const T *operand2, size_t uint_count, T *result)
{
    unsigned char carry = add_uint(*operand1++, *operand2++, result++);
    for (; --uint_count; operand1++, operand2++, result++)
    {
        T temp_result;
        carry = add_uint(*operand1, *operand2, carry, &temp_result);
        *result = temp_result;
    }
    return carry;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char sub_uint(T operand1, T operand2, T *result)
{
    *result = operand1 - operand2;
    return operand2 > operand1;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char sub_uint(T operand1, T operand2, unsigned char borrow, T *result)
{
    T diff = operand1 - operand2;
    *result = diff - (borrow != 0);
    return (diff > operand1) || (diff < borrow);
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline unsigned char sub_uint_base(const T *operand1, const T *operand2, size_t uint_count, T *result)
{
    unsigned char borrow = sub_uint(*operand1++, *operand2++, result++);
    for (; --uint_count; operand1++, operand2++, result++)
    {
        T temp_result;
        borrow = sub_uint(*operand1, *operand2, borrow, &temp_result);
        *result = temp_result;
    }
    return borrow;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline void set_zero_uint(size_t uint_count, T *result)
{
    std::fill_n(result, uint_count, static_cast<T>(0));
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline void divide_uint3_inplace(T *numerator, T denominator, T *quotient)
{
    size_t Tbitsz = sizeof(T) * 8;
    size_t uint_count = 3;
    quotient[0] = 0;
    quotient[1] = 0;
    quotient[2] = 0;

    int numerator_bits = get_significant_bit_count_uint(numerator, uint_count);
    int denominator_bits = get_significant_bit_count(denominator);

    if (numerator_bits < denominator_bits)
        return;

    uint_count = static_cast<size_t>((numerator_bits + Tbitsz - 1) / Tbitsz);
    if (uint_count == 1)
    {
        *quotient = *numerator / denominator;
        *numerator -= *quotient * denominator;
        return;
    }

    std::vector<T> shifted_denominator(uint_count, 0);
    shifted_denominator[0] = denominator;

    std::vector<T> difference(uint_count);
    int denominator_shift = numerator_bits - denominator_bits;

    heracles::math::left_shift_uint3(shifted_denominator.data(), denominator_shift, shifted_denominator.data());
    denominator_bits += denominator_shift;

    int remaining_shifts = denominator_shift;

    while (numerator_bits == denominator_bits)
    {
        if (heracles::math::sub_uint_base(numerator, shifted_denominator.data(), uint_count, difference.data()))
        {
            if (remaining_shifts == 0)
                break;
            heracles::math::add_uint_base(difference.data(), numerator, uint_count, difference.data());
            heracles::math::left_shift_uint3(quotient, 1, quotient);
            remaining_shifts--;
        }
        quotient[0] |= 1;
        numerator_bits = heracles::math::get_significant_bit_count_uint(difference.data(), uint_count);
        int numerator_shift = denominator_bits - numerator_bits;
        numerator_shift = std::min(numerator_shift, remaining_shifts);

        if (numerator_bits > 0)
        {
            left_shift_uint3(difference.data(), numerator_shift, numerator);
            numerator_bits += numerator_shift;
        }
        else
            heracles::math::set_zero_uint(uint_count, numerator);

        heracles::math::left_shift_uint3(quotient, numerator_shift, quotient);
        remaining_shifts -= numerator_shift;
    }
    if (numerator_bits > 0)
        heracles::math::right_shift_uint3(numerator, denominator_shift, numerator);
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline T multiply_uint_mod(const T operand1, const T operand2, const T modulus)
{
    if (modulus == 0)
        throw std::invalid_argument("modulus cannot be zero");

    T prod[2];
    multiply_uint(operand1, operand2, prod);

    // barrett reduction 32-bit
    T numerator[3]{ 0, 0, 1 };
    T quotient[3]{ 0, 0, 0 };

    heracles::math::divide_uint3_inplace(numerator, modulus, quotient);

    std::vector<T> const_ratio{ quotient[0], quotient[1], numerator[0] };

    T tmp1, tmp2[2], tmp3, carry[2];

    multiply_uint(prod[0], const_ratio[0], carry);

    heracles::math::multiply_uint(prod[0], const_ratio[1], tmp2);
    tmp3 = tmp2[1] + heracles::math::add_uint(tmp2[0], carry[1], &tmp1);

    heracles::math::multiply_uint(prod[1], const_ratio[0], tmp2);
    carry[1] = tmp2[1] + heracles::math::add_uint(tmp1, tmp2[0], &tmp1);

    tmp1 = prod[1] * const_ratio[1] + tmp3 + carry[1];
    tmp3 = prod[0] - tmp1 * modulus;

    return tmp3 >= modulus ? tmp3 - modulus : tmp3;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline T exponentiate_uint_mod(const T operand, T exponent, const T modulus)
{
    if (exponent == 0)
        return 1;
    if (exponent == 1)
        return operand;
    T power = operand;
    T product = 0;
    T intermediate = 1;
    while (true)
    {
        if (exponent & 1)
        {
            product = multiply_uint_mod(power, intermediate, modulus);
            std::swap(product, intermediate);
        }
        exponent >>= 1;
        if (exponent == 0)
            break;
        product = multiply_uint_mod(power, power, modulus);
        std::swap(product, power);
    }
    return intermediate;
}

std::tuple<uint64_t, int64_t, int64_t> xgcd(uint64_t x, uint64_t y);
std::tuple<uint32_t, int32_t, int32_t> xgcd(uint32_t x, uint32_t y);

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
inline bool try_invert_uint_mod(const T value, const T modulus, T *result)
{
    if (value == 0)
        return false;

    auto gcd_tuple = xgcd(value, modulus);
    if (std::get<0>(gcd_tuple) != 1)
        return false;
    else if (std::get<1>(gcd_tuple) < 0)
    {
        *result = static_cast<T>(std::get<1>(gcd_tuple)) + modulus;
        return true;
    }

    *result = static_cast<T>(std::get<1>(gcd_tuple));
    return true;
}

template <typename T, typename = std::enable_if_t<is_uint_v<T>>>
T get_invert_uint_mod(const T value, const T modulus)
{
    T result;
    if (!try_invert_uint_mod(value, modulus, &result))
    {
        std::ostringstream msg;
        msg << "Cannot invert value " << value << " with modulus " << modulus;
        throw std::runtime_error(msg.str());
    }

    return result;
}
std::uint32_t reverse_bits(const std::uint32_t operand, std::uint32_t bit_count = 32);

inline std::uint32_t montgomeryAdd(const std::uint32_t a, const std::uint32_t b, const std::uint32_t modulus)
{
    return heracles::math::add_uint_mod(a, b, modulus);
}

inline std::uint32_t montgomeryMul(
    const std::uint32_t a, const std::uint32_t b, const std::uint32_t modulus, bool use_mont = true)
{
    if (!use_mont)
        return a * b % modulus;

    std::uint32_t u[2];
    heracles::math::multiply_uint(a, b, u);

    std::uint32_t k = modulus - 2;
    std::uint32_t m[2];
    // u[0] = lower 32bit
    heracles::math::multiply_uint(u[0], k, m);

    // z = low 32bit m (m[0]) * modulus
    std::uint32_t z[2];
    heracles::math::multiply_uint(m[0], modulus, z);

    // _u = u + z
    std::uint32_t _u[2];
    heracles::math::add_uint_base(u, z, 2, _u);

    // return high 32bit (_u[1])
    return _u[1] < modulus ? _u[1] : _u[1] - modulus;
}
} // namespace heracles::math
