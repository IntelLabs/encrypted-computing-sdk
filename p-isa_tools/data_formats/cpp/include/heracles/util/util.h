// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <cstdint>
#include <iostream>
#include <string>
#include <tuple>
#include <unordered_set>
#include <utility>
#include <vector>
#include "heracles/data/math.h"
#include "heracles/proto/data.pb.h"
#include "heracles/proto/fhe_trace.pb.h"

namespace heracles::util
{
namespace data
{
    // some utility functions needed during HEC transformations

    // - montgomery transform
    //   - constants
    const uint64_t montgomery_R_bits = 32;
    const uint64_t montgomery_R = 1ULL << montgomery_R_bits;

    //   - single value
    // - montgomery transformation
    uint32_t convert_to_montgomery(const uint32_t num, const std::uint32_t modulus);
    // - montgomery to normal conversion
    uint32_t convert_to_normal(const uint32_t num, const std::uint32_t modulus);
    uint32_t convert_to_normal_inv_r(const uint32_t num, const std::uint32_t inv_r, const std::uint32_t modulus);

    // - bit-reversal
    //   - shuffle power-of-two-sized poly vector according to bit-reversal of index
    //     Note: we assume dst is allocated object but does not contain anything!
    void poly_bit_reverse(heracles::data::RNSPolynomial *dst, const heracles::data::RNSPolynomial &src);
    void poly_bit_reverse(heracles::data::RNSPolynomial *dst, const std::vector<uint32_t> &src);
    void poly_bit_reverse_inplace(heracles::data::RNSPolynomial *src);

    void transform_and_flatten_key_switch(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::KeySwitch &data);
    void transform_and_flatten_ciphertext(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Ciphertext &data);
    void transform_and_flatten_plaintext(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Plaintext &data);
    void transform_and_flatten_dcrtpoly(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::DCRTPoly &data);
    void transform_and_flatten_poly(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Polynomial &poly);

    void convert_rnspoly_to_original(heracles::data::RNSPolynomial *dest, const heracles::data::RNSPolynomial &src);

    std::tuple<std::string, uint32_t, uint32_t> split_symbol_name(const std::string &sym);
    // convert protobuf map of Array field to index vector
    std::vector<std::uint32_t> toIndex(const std::string &key);
    std::string toStrKey(const std::vector<size_t> &indices);
} // namespace data

namespace fhe_trace
{
    constexpr char DELIMITER = ',';

    /*
            Print single instruction
        */
    void print_instruction(
        const heracles::fhe_trace::Instruction &inst, const std::string &header = "", bool printBKops = false);

    std::ostream &operator<<(std::ostream &out, const heracles::fhe_trace::Instruction &inst);

    /*
            Print trace
        */
    void print_trace(const heracles::fhe_trace::Trace &trace);

    /*
            Get input(s) and output symbols of instruction pb
        */
    std::pair<std::vector<std::string>, std::vector<std::string>> get_symbols(
        const heracles::fhe_trace::Instruction &inst);

    /*
            Get all input(s) and output symbols of trace pb
            If exclusive_outputs==true, return outputs that are never used as inputs
        */
    std::pair<std::unordered_set<std::string>, std::unordered_set<std::string>> get_all_symbols(
        const heracles::fhe_trace::Trace &trace, bool exclusive_outputs = false);

} // namespace fhe_trace
} // namespace heracles::util
