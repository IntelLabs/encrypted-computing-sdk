// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_instruction_tests/pisa_instruction_test.h"
#include <algorithm>
#include <iostream>
#include <map>
#include <math.h>
#include <random>
#include <string>

class RandomStreamInstructionTest : public PisaInstructionTest
{
public:
    static std::string operationName();

    RandomStreamInstructionTest();
    ;

    // PisaKernelTest interface
public:
    void constructTest() override;

    pisa::PISAInstruction *createInstr(std::string op, std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createAddInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createMulInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createMacInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createMaciInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createMuliInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createSubInstr(std::string output, std::string input0, std::string input1);
    pisa::PISAInstruction *createCopyInstr(std::string output, std::string input0);
};

inline std::string RandomStreamInstructionTest::operationName()
{
    return "random_stream_instruction";
}

inline RandomStreamInstructionTest::RandomStreamInstructionTest() :
    PisaInstructionTest()
{
    configuration["Name"]                   = this->operationName();
    configuration["Intermediate_registers"] = "10";
    configuration["Add_ops"]                = "5";
    configuration["Mul_ops"]                = "0";
    configuration["Copy_ops"]               = "0";
    configuration["Mac_ops"]                = "0";
    configuration["Maci_ops"]               = "0";
    configuration["Muli_ops"]               = "0";
    configuration["Sub_ops"]                = "0";
    configuration["Random_seed"]            = "0";
}

inline void RandomStreamInstructionTest::constructTest()
{

    unsigned int random_seed = std::stoi(configuration["Random_seed"]);
    std::cout << "Entered Construct Test" << std::endl;
    std::cout << "Configuration:" << std::endl;
    for (auto config : configuration)
    {
        std::cout << config.first << " : " << config.second << std::endl;
    }

    std::vector<std::string> output_regs = { "output0" };
    std::vector<std::string> intermediate_regs;
    int intermediate_register_count = std::stoi(configuration["Intermediate_registers"]);
    for (unsigned int x = 0; x < intermediate_register_count; x++)
    {
        intermediate_regs.push_back("intermediate" + std::to_string(x));
    }
    std::vector<std::string> input_regs = { { "input0" }, { "input1" } };

    std::vector<std::string> op_tokens;

    //Initialize all intermediates with 1 value
    instruction_trace.push_back(createInstr("copy", intermediate_regs[0], input_regs[0], input_regs[0]));
    for (unsigned int x = 1; x < intermediate_regs.size(); x++)
    {
        instruction_trace.push_back(createInstr("copy", intermediate_regs[x], intermediate_regs[x - 1], intermediate_regs[x - 1]));
    }

    //Create a bucket of test tokens
    //Add ops
    int add_ops = std::stoi(configuration["Add_ops"]);
    for (unsigned int x = 0; x < add_ops; x++)
    {
        op_tokens.push_back("add");
    }
    int mul_ops = std::stoi(configuration["Mul_ops"]);
    for (unsigned int x = 0; x < mul_ops; x++)
    {
        op_tokens.push_back("mul");
    }
    int copy_ops = std::stoi(configuration["Copy_ops"]);
    for (unsigned int x = 0; x < copy_ops; x++)
    {
        op_tokens.push_back("copy");
    }
    int mac_ops = std::stoi(configuration["Mac_ops"]);
    for (unsigned int x = 0; x < mac_ops; x++)
    {
        op_tokens.push_back("mac");
    }
    int maci_ops = std::stoi(configuration["Maci_ops"]);
    for (unsigned int x = 0; x < maci_ops; x++)
    {
        op_tokens.push_back("maci");
    }
    int muli_ops = std::stoi(configuration["Muli_ops"]);
    for (unsigned int x = 0; x < muli_ops; x++)
    {
        op_tokens.push_back("muli");
    }
    int sub_ops = std::stoi(configuration["Sub_ops"]);
    for (unsigned int x = 0; x < sub_ops; x++)
    {
        op_tokens.push_back("sub");
    }

    //Shuffle the bucket
    std::random_shuffle(op_tokens.begin() + intermediate_regs.size(), op_tokens.end());

    //Create first instruction
    auto first_token = op_tokens.front();
    int output_reg   = rand_r(&random_seed) % intermediate_regs.size();
    if (op_tokens.size() > 1)
    {
        instruction_trace.push_back(createInstr(first_token, intermediate_regs[output_reg], intermediate_regs.back(), input_regs[1]));
    }
    else
    {
        instruction_trace.push_back(createInstr(first_token, output_regs[0], input_regs[0], input_regs[1]));
    }
    //create intermediate instructions
    int next_reg = rand_r(&random_seed) % intermediate_regs.size();
    for (int x = 1; x < op_tokens.size() - 1; x++)
    {
        instruction_trace.push_back(createInstr(op_tokens[x], intermediate_regs[next_reg], intermediate_regs[output_reg], intermediate_regs[rand() % intermediate_regs.size()]));
        output_reg = next_reg;
        next_reg   = rand_r(&random_seed) % intermediate_regs.size();
    }

    //create final instruction
    auto final_token = op_tokens.back();
    if (op_tokens.size() > 1)
    {
        instruction_trace.push_back(createInstr(final_token, output_regs[0], intermediate_regs[output_reg], intermediate_regs[rand() % intermediate_regs.size()]));
    }

    // }
    created = true;
    // std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createInstr(std::string op, std::string output, std::string input0, std::string input1)
{
    pisa::PISAInstruction *instr;
    if (op == "add")
    {
        instr = createAddInstr(output, input0, input1);
    }
    else if (op == "mul")
    {
        instr = createMulInstr(output, input0, input1);
    }
    else if (op == "copy")
    {
        instr = createCopyInstr(output, input0);
    }
    else if (op == "mac")
    {
        instr = createMacInstr(output, input0, input1);
    }
    else if (op == "maci")
    {
        instr = createMaciInstr(output, input0, input1);
    }
    else if (op == "muli")
    {
        instr = createMuliInstr(output, input0, input1);
    }
    else if (op == "sub")
    {
        instr = createSubInstr(output, input0, input1);
    }

    return instr;
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createAddInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Add(std::stoi(configuration["Poly_mod_log2"]),
                                      pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createMulInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Mul(std::stoi(configuration["Poly_mod_log2"]),
                                      pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createMacInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Mac(std::stoi(configuration["Poly_mod_log2"]),
                                      pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createMaciInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Maci(std::stoi(configuration["Poly_mod_log2"]),
                                       pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createMuliInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Muli(std::stoi(configuration["Poly_mod_log2"]),
                                       pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createSubInstr(std::string output, std::string input0, std::string input1)
{
    return new pisa::instruction::Sub(std::stoi(configuration["Poly_mod_log2"]),
                                      pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      pisa::Operand(input1 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                      std::stoi(configuration["RNS_INDEX"]));
}

inline pisa::PISAInstruction *RandomStreamInstructionTest::createCopyInstr(std::string output, std::string input0)
{
    return new pisa::instruction::Copy(std::stoi(configuration["Poly_mod_log2"]),
                                       pisa::Operand(output + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]),
                                       pisa::Operand(input0 + "_" + configuration["RNS_INDEX"] + "_" + configuration["Chunk_INDEX"]));
}
