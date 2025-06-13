// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <string>
#include <tuple>
#include <vector>

namespace pisa::poly {

enum class OPERAND_TYPE
{
    POLYNOMIAL,
    IMMEDIATE
};

class Polynomial
{
public:
    Polynomial() {}
    Polynomial(std::string _name)
    {
        register_name = _name;
    }
    Polynomial(std::string _name, int _num_of_rns_terms, int _num_of_polynomials)
    {
        register_name      = _name;
        num_of_polynomials = _num_of_polynomials;
        num_of_rns_terms   = _num_of_rns_terms;
    }
    static std::tuple<std::string, int, int> decomposePolyStringForm(std::string polyString)
    {
        int first_delim_pos  = polyString.find('-', 0);
        int second_delim_pos = polyString.find('-', first_delim_pos + 1);

        std::string label = polyString.substr(0, first_delim_pos);
        int poly_parts    = std::stoi(polyString.substr(first_delim_pos + 1, second_delim_pos - first_delim_pos));
        int rns_num       = std::stoi(polyString.substr(second_delim_pos + 1, polyString.npos - second_delim_pos));

        return { label, poly_parts, rns_num };
    }

    std::string location() { return register_name; }
    bool immediate() { return operand_type == OPERAND_TYPE::IMMEDIATE; }
    std::string register_name;
    bool in_ntt_form          = false;
    bool in_montgomery_form   = true;
    int num_of_polynomials    = 2;
    int num_of_rns_terms      = 1;
    int num_of_coefficients   = 8192;
    OPERAND_TYPE operand_type = OPERAND_TYPE::POLYNOMIAL;

private:
    std::vector<std::vector<std::vector<int64_t>>> data_poly_rns_coefficient;
};

} // namespace pisa::poly
