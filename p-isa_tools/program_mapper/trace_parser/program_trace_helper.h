// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <program_mapper/poly_program/polyprogram.h>
#ifdef ENABLE_DATA_FORMATS
#include <heracles/heracles_proto.h>
#endif

enum POLYNOMIAL_PROGRAM_FORMAT
{
    PROTOBUFF,
    CSV
};

inline std::string trim(const std::string &component)
{
    std::string res;
    std::copy_if(component.cbegin(), component.cend(), std::back_inserter(res),
                 [](const char c) { return c != '\n' && c != '\r'; });
    return res;
}

struct PolynomialProgramHelper
{
    PolynomialProgramHelper() = default;

    static std::shared_ptr<pisa::poly::PolyProgram> parse(const std::string &filename_or_prefix, POLYNOMIAL_PROGRAM_FORMAT format = CSV, bool ignore_header = true);
    static std::shared_ptr<pisa::poly::PolyProgram> parseCSV(const std::string &filename, bool ignore_header = true);
    static void writeTraceToCSV(const std::shared_ptr<pisa::poly::PolyProgram> trace, std::string file_name);

#ifdef ENABLE_DATA_FORMATS
    static std::shared_ptr<pisa::poly::PolyProgram> parse(const heracles::fhe_trace::Trace &trace_pb, bool verbose = false);
    static std::shared_ptr<pisa::poly::PolyProgram> parseProtoBuff(const std::string &filename, bool verbose = false);
    static void writeTraceToProtoBuff(const std::shared_ptr<pisa::poly::PolyProgram> trace, std::string file_name);
#endif

    static std::shared_ptr<pisa::poly::PolyOperation> parseInstruction(const std::vector<std::string> &components, std::shared_ptr<pisa::poly::PolyProgram> program);
    static std::vector<std::string> writeToASCIIComponents(const std::shared_ptr<pisa::poly::PolyOperation> operation);

#ifdef ENABLE_DATA_FORMATS
    static std::shared_ptr<pisa::poly::PolyOperation> parseInstruction(const heracles::fhe_trace::Instruction &instruction_pb);
#endif
    static void parseComponent(const std::string &component, PARAM_TYPE type, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void extractComponent(const std::shared_ptr<pisa::poly::PolyOperation> instr, std::string &component, int component_index);
#ifdef ENABLE_DATA_FORMATS
    static heracles::fhe_trace::Instruction *getProtobuffInstruction(std::shared_ptr<pisa::poly::PolyOperation> instr);
#endif
    //CSV Parsing functions
    static void parse_OP_NAME(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_CIPHER_DEGREE(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_INPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_OUTPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_INPUT_OUTPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_POLYMOD_DEG_LOG2(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_RNS_TERM(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_FHE_SCHEME(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_GALOIS_ELT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_FACTOR(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_KEY_RNS(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr);
    static void parse_PARAM(const std::pair<std::string, std::pair<std::string, pisa::poly::ValueType>> component, std::shared_ptr<pisa::poly::PolyOperation> instr);

    //CSV Writing functions
    static void extract_OP_NAME(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_CIPHER_DEGREE(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_INPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_OUTPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_INPUT_OUTPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_POLYMOD_DEG_LOG2(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_RNS_TERM(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_FHE_SCHEME(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_GALOIS_ELT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_FACTOR(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_KEY_RNS(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);
    static void extract_PARAM(std::pair<std::string, std::pair<std::string, pisa::poly::ValueType>> &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index);

    constexpr static int OP_CODE_LOCATION = 0;
};
