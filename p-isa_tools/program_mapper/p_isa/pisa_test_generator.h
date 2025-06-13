// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/tests/pisa_instruction_tests.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests.h"
#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <nlohmann/json.hpp>
#include <program_mapper/poly_program/polyprogram.h>
#include <vector>

using json = nlohmann::json;
namespace pisa::testgenerator {

enum class InputGenerationMode
{
    SINGLE_ONE,
    ALL_ONES,
    ASCENDING_FROM_ZERO,
    ONE_RANDOM,
    ALL_RANDOM
};

static std::string AvailableGenerationModesStr()
{
    std::string genModes = "( SINGLE_ONE , ALL_ONES , ASCENDING_FROM_ZERO , ONE_RANDOM , ALL_RANDOM )";
    return genModes;
}
} // namespace pisa::testgenerator

class PisaTestGenerator
{
public:
    PisaTestGenerator();

    graph::Graph<pisa::PISAInstruction> generateGraphFromProgramTrace(ProgramTrace program_trace);
    graph::Graph<pisa::PISAInstruction> generateGraphFromHEOperationTrace(std::vector<pisa::poly::PolyOperation *> program_trace);
    graph::Graph<pisa::PISAInstruction> generateGraphFromPISAInstructions(std::vector<pisa::PISAInstruction *> instructions);
    void populateCalculatedOutputResults(std::vector<pisa::PISAInstruction *> instructions, json &input);
    json generateJSONForGraph(graph::Graph<pisa::PISAInstruction> p_isa_graph, pisa::testgenerator::InputGenerationMode gen_mode = pisa::testgenerator::InputGenerationMode::SINGLE_ONE, unsigned int random_seed = 0);
    int findMaxRNSNumber(json &input_json);
    void addMetaDataInformation(json &input_json, int RNS_NUM);
    void addMetaDataInformation(json &input_json);
    void convertPolyRnsChunkToPolyRns(json &input_json);
    void convertPolyRnsChunkToPolyRnsHelper(json &input_json);
    void writeJSON(json input_json, std::string file_name);
    json trace_file;

    int block_size    = 8192;
    int modulus_value = 32684;
};
