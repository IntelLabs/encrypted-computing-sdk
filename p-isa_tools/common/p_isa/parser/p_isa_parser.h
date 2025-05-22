// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <string>
#include <vector>

#include <common/p_isa/p_isa.h>

namespace pisa {

class PISAParser
{
public:
    PISAParser() = delete;
    static std::vector<PISAInstruction *> parse(const std::string &filename);

private:
    static constexpr int OP_CODE_LOCATION = 1;

    static PISAInstruction *parseInstruction(const std::vector<std::string> &components);

    static void parseInstruction(const std::string &, pisa::PARAM_TYPE, pisa::PISAInstruction *instr);

    static void parseComponent(const std::string &component, pisa::PARAM_TYPE type, pisa::PISAInstruction *instr);
    static void parse_OP_NAME(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_INPUT_OPERAND(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_IMMEDIATE(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_OUTPUT_OPERAND(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_INPUT_OUTPUT_OPERAND(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_POLYMOD_DEG_LOG2(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_RESIDUAL(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_ADDITIONAL_PARAMS(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_W_PARAM(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_GALOIS_ELEMENT(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_GROUP_ID(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_STAGE(const std::string &component, pisa::PISAInstruction *instr);
    static void parse_BLOCK(const std::string &component, pisa::PISAInstruction *instr);
};
} // namespace pisa
