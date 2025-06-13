// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <string>
#include <vector>

namespace pisa::poly {

enum PARAM_TYPE
{
    OP_NAME,
    INPUT_ARGUMENT,
    OUTPUT_ARGUMENT,
    INPUT_OUTPUT_ARGUMENT,
    POLYMOD_DEG_LOG2,
    CIPHER_DEGREE,
    RNS_TERM,
    FHE_SCHEME,
    PARAM,
    GALOIS_ELT,
    FACTOR,
    KEY_RNS,
    ALPHA,
    QSIZE,
    DNUM,
};

/**
 * @brief The InstructionDesc struct stores a vector of param type objects used to describe the type of parameter in each location of an instruction
 */
struct OperationDesc
{
    OperationDesc() = default;
    OperationDesc(const std::initializer_list<PARAM_TYPE> &_params) :
        params(_params)
    {
    }
    std::vector<PARAM_TYPE> params;
};
struct PolyOperationDesc
{
    PolyOperationDesc() {}
    PolyOperationDesc(std::string _name, OperationDesc _desc) :
        name(_name), desc(_desc) {}
    std::string name;
    OperationDesc desc;
    bool force_desc_op_name = true;
};
} // namespace pisa::poly
