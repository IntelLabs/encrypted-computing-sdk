
// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

namespace pisa::utility {

/**
 * @brief reverseBits is a utility function to reverse the order of bits of a number mod some value
 * @param i The number to reverse
 * @param mod The number of bits in i to reverse
 * @return
 */
template <typename T>
static T reverseBits(T i, int mod)
{
    unsigned int s    = sizeof(i) * 8;
    unsigned int mask = ~0;
    while ((s >>= 1) > 0)
    {
        mask ^= (mask << s);
        i = ((i >> s) & mask) | ((i << s) & ~mask);
    }

    T shifted = i >> (sizeof(i) * 8 - mod);
    return shifted;
}

} // namespace pisa::utility
