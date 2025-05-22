// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>

#include <common/string.h>

#include "p_isa_parser.h"

std::vector<pisa::PISAInstruction *> pisa::PISAParser::parse(const std::string &filename)
{
    try
    {
        std::vector<pisa::PISAInstruction *> instructions;
        std::ifstream file(filename);
        if (!file.is_open())
        {
            throw std::runtime_error("File not found: " + filename);
        }

        std::string current_line;
        while (std::getline(file, current_line))
        {
            std::vector<std::string> components;
            std::istringstream current_line_ss(current_line);

            std::string component;
            while (std::getline(current_line_ss, component, ','))
            {
                components.push_back(std::move(component));
            }
            instructions.push_back(parseInstruction(components));
        }
        return instructions;
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during parse, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << " in file " << __FILE__ << std::endl;
        throw;
    }
}

pisa::PISAInstruction *pisa::PISAParser::parseInstruction(const std::vector<std::string> &components)
{
    try
    {
        std::string operation            = whiteSpaceRemoved(components[OP_CODE_LOCATION]);
        auto instruction_instance        = InstructionMap.at(operation);
        PISAInstruction *new_instruction = instruction_instance->create();
        for (int x = 0; x < components.size(); x++)
        {
            parseComponent(components[x], new_instruction->getDescription().params[x], new_instruction);
        }

        return new_instruction;
    }
    catch (const std::out_of_range &err)
    {
        std::cerr << "No Instruction Desc found for operation in InstructionMap map. Operation: "
                  << components[OP_CODE_LOCATION]
                  << std::endl;
    }
    catch (...)
    {
        std::cerr << "Invalid instruction detected during parsing.";
        throw;
    }
    throw;
}

void pisa::PISAParser::parseComponent(const std::string &component, PARAM_TYPE type, PISAInstruction *instr)
{
    switch (type)
    {
    case pisa::GROUP_ID:
        parse_GROUP_ID(component, instr);
        break;
    case pisa::STAGE:
        parse_STAGE(component, instr);
        break;
    case pisa::BLOCK:
        parse_BLOCK(component, instr);
        break;
    case pisa::IMMEDIATE:
        parse_IMMEDIATE(component, instr);
        break;
    case pisa::W_PACKED_PARAM:
        parse_W_PARAM(component, instr);
        break;
    case pisa::INPUT_OUTPUT_OPERAND:
        parse_INPUT_OUTPUT_OPERAND(component, instr);
        break;
    case pisa::OP_NAME:
        parse_OP_NAME(component, instr);
        break;
    case pisa::INPUT_OPERAND:
        parse_INPUT_OPERAND(component, instr);
        break;
    case pisa::OUTPUT_OPERAND:
        parse_OUTPUT_OPERAND(component, instr);
        break;
    case pisa::POLYMOD_DEG_LOG2:
        parse_POLYMOD_DEG_LOG2(component, instr);
        break;
    case pisa::RESIDUAL:
        parse_RESIDUAL(component, instr);
        break;
    case pisa::GALOIS_ELEMENT:
        parse_GALOIS_ELEMENT(component, instr);
        break;
    case pisa::ADDITIONAL_PARAMS:
        parse_ADDITIONAL_PARAMS(component, instr);
        break;
    default:
        throw std::logic_error("Unhandled component during parsing");
    }
}

void pisa::PISAParser::parse_OP_NAME(const std::string &component, PISAInstruction *instr)
{
    instr->setName(whiteSpaceRemoved(component));
}

void pisa::PISAParser::parse_INPUT_OPERAND(const std::string &component, PISAInstruction *instr)
{
    instr->addInputOperand(Operand(component));
}

void pisa::PISAParser::parse_IMMEDIATE(const std::string &component, PISAInstruction *instr)
{
    auto trimmed = whiteSpaceRemoved(component);
    instr->addInputOperand(Operand(trimmed, true));
}

void pisa::PISAParser::parse_OUTPUT_OPERAND(const std::string &component, PISAInstruction *instr)
{
    instr->addOutputOperand(Operand(component));
}

void pisa::PISAParser::parse_INPUT_OUTPUT_OPERAND(const std::string &component, PISAInstruction *instr)
{
    instr->addInputOperand(Operand(component));
    instr->addOutputOperand(Operand(component));
}

void pisa::PISAParser::parse_POLYMOD_DEG_LOG2(const std::string &component, PISAInstruction *instr)
{
    instr->setPMD(std::stoi(component));
}

void pisa::PISAParser::parse_RESIDUAL(const std::string &component, PISAInstruction *instr)
{
    instr->setResidual(std::stoi(component));
}

// TODO: to be investigated a bit more
void pisa::PISAParser::parse_GALOIS_ELEMENT(const std::string &component, PISAInstruction *instr)
{
    instr->setGalois_element(std::stoi(component));
}

void pisa::PISAParser::parse_GROUP_ID(const std::string &component, PISAInstruction *instr)
{
    instr->setGroupId(std::stoi(component));
}

void pisa::PISAParser::parse_STAGE(const std::string &component, PISAInstruction *instr)
{
    instr->setStage(std::stoi(component));
}

void pisa::PISAParser::parse_BLOCK(const std::string &component, PISAInstruction *instr)
{
    instr->setBlock(std::stoi(component));
}

void pisa::PISAParser::parse_ADDITIONAL_PARAMS(const std::string &component, PISAInstruction *instr)
{
    throw std::logic_error("parse_ADDITIONAL_PARAMS not implemented.");
}

void pisa::PISAParser::parse_W_PARAM(const std::string &component, PISAInstruction *instr)
{
    instr->setWParam(WParam(component));
}
