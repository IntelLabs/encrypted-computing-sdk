// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_instruction_tests/pisa_instruction_test.h"
#include <iostream>
#include <map>
#include <math.h>
#include <string>

class subInstructionTest : public PisaInstructionTest
{
public:
    static std::string operationName() { return "sub_instruction"; }

    subInstructionTest() :
        PisaInstructionTest()
    {
        configuration["Name"] = this->operationName();
    };

    // PisaKernelTest interface
public:
    void constructTest() override
    {
        std::cout << "Entered Construct Test" << std::endl;
        std::cout << "Configuration:" << std::endl;
        for (auto config : configuration)
        {
            std::cout << config.first << " : " << config.second << std::endl;
        }

        std::vector<std::string> output_regs = { "output0" };
        std::vector<std::string> input_regs  = { { "input0" }, { "input1" } };

        auto instr = new pisa::instruction::Sub(std::stoi(configuration["Poly_mod_log2"]),
                                                pisa::Operand(output_regs[0] + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                                pisa::Operand(input_regs[0] + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                                pisa::Operand(input_regs[1] + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                                std::stoi(configuration["RNS_INDEX"]));

        instruction_trace.push_back(instr);

        // }
        created = true;
        // std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
