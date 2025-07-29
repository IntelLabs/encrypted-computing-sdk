// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/util/util.h"
#include <assert.h>
#include <cmath>

namespace hmath = heracles::math;

namespace heracles::util
{
namespace data
{
    // some utility functions needed during HEC transformations

    // - montgomery transformation
    uint32_t convert_to_montgomery(const uint32_t num, const std::uint32_t modulus)
    {
        return static_cast<uint32_t>((static_cast<uint64_t>(num) << 32) % modulus);
    }

    // - montgomery to normal conversion
    uint32_t convert_to_normal(const uint32_t num, const std::uint32_t modulus)
    {
        uint64_t inv_r = 0;
        hmath::try_invert_uint_mod(montgomery_R, static_cast<uint64_t>(modulus), &inv_r); // 64
        return hmath::multiply_uint_mod(num, static_cast<uint32_t>(inv_r), modulus);
    }

    uint32_t convert_to_normal_inv_r(const uint32_t num, const std::uint32_t inv_r, const std::uint32_t modulus)
    {
        return hmath::multiply_uint_mod(num, inv_r, modulus);
    }

    void poly_bit_reverse(heracles::data::RNSPolynomial *dst, const heracles::data::RNSPolynomial &src)
    {
        std::size_t degree = src.coeffs_size();
        std::size_t logDegree = log2(degree);
        if (degree != static_cast<std::size_t>(1 << logDegree))
            throw std::runtime_error("RNS polynomial degree mismatch");

        std::vector<uint32_t> tmp(degree);

#pragma omp parallel for
        for (size_t i = 0; i < degree; i++)
        {
            tmp[i] = src.coeffs(hmath::reverse_bits(i, logDegree));
        }
        *(dst->mutable_coeffs()) = { tmp.begin(), tmp.end() };
        dst->set_modulus(src.modulus());
    }

    void poly_bit_reverse(heracles::data::RNSPolynomial *dst, const std::vector<uint32_t> &src)
    {
        std::size_t degree = src.size();
        std::size_t logDegree = log2(degree);
        if (degree != static_cast<std::size_t>(1 << logDegree))
            throw std::runtime_error("RNS polynomial degree mismatch");

        std::vector<uint32_t> tmp(degree);

#pragma omp parallel for
        for (size_t i = 0; i < degree; i++)
        {
            tmp[i] = src[hmath::reverse_bits(i, logDegree)];
        }
        *(dst->mutable_coeffs()) = { tmp.begin(), tmp.end() };
    }

    void poly_bit_reverse_inplace(heracles::data::RNSPolynomial *src)
    {
        heracles::data::RNSPolynomial tmp;
        poly_bit_reverse(&tmp, *src);
        *src = tmp;
    }

    void transform_and_flatten_key_switch(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::KeySwitch &data)
    {
        for (int d = 0; d < data.digits_size(); ++d)
        {
            for (int p = 0; p < data.digits(d).polys_size(); ++p)
            {
                std::string flatten_prefix = prefix + "_" + std::to_string(p) + "_" + std::to_string(d);
                transform_and_flatten_poly(poly_symbols, flatten_prefix, data.digits(d).polys(p));
            }
        }
    }

    void transform_and_flatten_ciphertext(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Ciphertext &data)
    {
        for (int p = 0; p < data.polys_size(); ++p)
        {
            std::string flatten_prefix = prefix + "_" + std::to_string(p);
            transform_and_flatten_poly(poly_symbols, flatten_prefix, data.polys(p));
        }
    }

    void transform_and_flatten_plaintext(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Plaintext &data)
    {
        transform_and_flatten_poly(poly_symbols, prefix, data.poly());
    }

    void transform_and_flatten_dcrtpoly(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::DCRTPoly &data)
    {
        for (int p = 0; p < data.polys_size(); ++p)
        {
            std::string flatten_prefix = prefix + "_" + std::to_string(p);
            transform_and_flatten_poly(poly_symbols, flatten_prefix, data.polys(p));
        }
    }

    void transform_and_flatten_poly(
        heracles::data::PolySymbols *poly_symbols, const std::string &prefix, const heracles::data::Polynomial &poly)
    {
        for (int r = 0; r < poly.rns_polys_size(); ++r)
        {
            std::string poly_prefix = prefix + "_" + std::to_string(r);
            auto sym_poly_map = poly_symbols->mutable_sym_poly_map();
            std::vector<uint32_t> tmp(poly.rns_polys(r).coeffs_size());
#pragma omp parallel for
            for (int j = 0; j < poly.rns_polys(r).coeffs_size(); ++j)
                tmp[j] = convert_to_montgomery(poly.rns_polys(r).coeffs(j), poly.rns_polys(r).modulus());

            poly_bit_reverse(&(*sym_poly_map)[poly_prefix], tmp);
            (*sym_poly_map)[poly_prefix].set_modulus(poly.rns_polys(r).modulus());
        }
    }

    void convert_rnspoly_to_original(heracles::data::RNSPolynomial *dest, const heracles::data::RNSPolynomial &src)
    {
        uint64_t inv_r = 0;
        hmath::try_invert_uint_mod(montgomery_R, static_cast<uint64_t>(src.modulus()), &inv_r);

        dest->set_modulus(src.modulus());
        std::vector<uint32_t> tmp(src.coeffs_size());
#pragma omp parallel for
        for (int j = 0; j < src.coeffs_size(); ++j)
            tmp[j] = convert_to_normal_inv_r(src.coeffs(j), static_cast<uint32_t>(inv_r), src.modulus());

        poly_bit_reverse(dest, tmp);
    }

    std::tuple<std::string, uint32_t, uint32_t> split_symbol_name(const std::string &sym)
    {
        std::vector<std::string> buf;

        unsigned int loc = -1, prev_loc = 0;
        do
        {
            loc = sym.find('_', loc + 1);

            auto tmp = sym.substr(prev_loc, loc == std::string::npos ? std::string::npos : loc - prev_loc);
            buf.push_back(tmp);
            prev_loc = loc + 1;
        } while (loc != std::string::npos && buf.size() <= 2);

        if (buf.size() != 3)
            throw std::runtime_error("Symbol name is not in correct form");

        return { buf[0], std::stoul(buf[1]), std::stoul(buf[2]) };
    }

    std::vector<std::uint32_t> toIndex(const std::string &key)
    {
        std::istringstream ss(key);
        std::vector<std::uint32_t> indices;
        std::string buf;
        while (std::getline(ss, buf, '_'))
        {
            // skip if not digit
            if (buf.find_first_not_of("0123456789") == std::string::npos)
                indices.push_back(std::stoul(buf));
        }
        return indices;
    }

    std::string toStrKey(const std::vector<size_t> &indices)
    {
        std::ostringstream key;
        std::string sep = "";
        for (const auto &idx : indices)
        {
            key << sep << idx;
            sep = "_";
        }
        return key.str();
    }
} // namespace data

namespace fhe_trace
{
    void print_instruction(const heracles::fhe_trace::Instruction &inst, const std::string &header, bool printBKops)
    {
        if (printBKops || inst.op().substr(0, 3) != "bk_")
            std::cout << header << (header.length() > 0 ? " " : "") << inst << std::endl;
    }

    std::ostream &operator<<(std::ostream &out, const heracles::fhe_trace::Instruction &inst)
    {
        std::string op = inst.op();
        out << op << DELIMITER;

        auto dest = inst.args().dests(0);
        out << dest.symbol_name() << DELIMITER << dest.num_rns() << DELIMITER << dest.order() << DELIMITER;

        for (const auto &src : inst.args().srcs())
        {
            out << src.symbol_name() << DELIMITER << src.num_rns() << DELIMITER << src.order() << DELIMITER;
        }

        for (const auto &[k, v] : inst.args().params())
        {
            out << v.value() << DELIMITER;
        }

        return out;
    }

    void print_trace(const heracles::fhe_trace::Trace &trace)
    {
        std::string scheme = heracles::common::Scheme_descriptor()->FindValueByNumber(trace.scheme())->name();
        scheme = scheme.substr(7); // Remove "SCHEME_" prefix
        std::uint32_t N = trace.n();

        size_t sz_instructions = trace.instructions_size();
        for (size_t i = 0; i < sz_instructions; ++i)
        {
            auto inst = trace.instructions(i);

            std::cout << i << ":";
            std::cout << scheme << DELIMITER << N << DELIMITER << inst << std::endl;
        }
    }

    std::pair<std::vector<std::string>, std::vector<std::string>> get_symbols(
        const heracles::fhe_trace::Instruction &inst)
    {
        std::pair<std::vector<std::string>, std::vector<std::string>> res;

        for (const auto &dest : inst.args().dests())
            res.second.push_back(dest.symbol_name());

        for (const auto &src : inst.args().srcs())
            res.first.push_back(src.symbol_name());

        return res;
    }
    std::pair<std::unordered_set<std::string>, std::unordered_set<std::string>> get_all_symbols(
        const heracles::fhe_trace::Trace &trace, bool exclusive_outputs)
    {
        std::unordered_set<std::string> symbols_input;
        std::unordered_set<std::string> symbols_output;
        for (const auto &instruction : trace.instructions())
        {
            std::string op = instruction.op();
            if (op.substr(0, 3) == "bk_")
                continue;

            auto [src_symbols, dest_symbols] = get_symbols(instruction);
            for (const std::string &sym : src_symbols)
                symbols_input.insert(sym);
            for (const std::string &sym : dest_symbols)
                symbols_output.insert(sym);
        }
        if (exclusive_outputs)
        {
            std::unordered_set<std::string> tmp;
            std::set_difference(
                symbols_output.begin(), symbols_output.end(), symbols_input.begin(), symbols_input.end(),
                std::inserter(tmp, tmp.begin()));
            symbols_output = tmp;
        }

        return std::make_pair(symbols_input, symbols_output);
    }
} // namespace fhe_trace
} // namespace heracles::util
