// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "isa_instruction.h"

namespace pisa {
/**
 * @brief The PARAM_TYPE enum used to indicate the type of a parameter during instruction parsing
 */
enum PARAM_TYPE
{
    OP_NAME,
    INPUT_OPERAND,
    OUTPUT_OPERAND,
    INPUT_OUTPUT_OPERAND,
    POLYMOD_DEG_LOG2,
    RESIDUAL,
    W_PACKED_PARAM,
    IMMEDIATE,
    GROUP_ID,
    STAGE,
    BLOCK,
    // temporary
    GALOIS_ELEMENT,
    ADDITIONAL_PARAMS
};

enum class INSTRUCTIONS
{
};

/**
 * @brief The InstructionDesc struct stores a vector of param type objects used to describe the type of parameter in each location of an instruction
 */
struct InstructionDesc
{
    InstructionDesc() = default;
    InstructionDesc(const std::initializer_list<PARAM_TYPE> &_params) :
        params(_params) {}

    std::vector<PARAM_TYPE> params;
};

/**
 * @brief The WParam class
 * w_<res>_<stage>_<block>
 */
class WParam
{
public:
    WParam() = default;

    WParam(const std::string &w_param)
    {
        std::stringstream splitter(w_param);
        std::string token;
        //Remove preamble
        std::getline(splitter, token, '_');

        //Get the residual
        std::getline(splitter, token, '_');
        m_residual = stoi(token);

        //Get stage
        std::getline(splitter, token, '_');
        m_stage = stoi(token);

        //block
        std::getline(splitter, token);
        m_block = stoi(token);
    }

    friend std::ostream &operator<<(std::ostream &stream, WParam op)
    {
        stream << "w_" << op.residual() << "_" << op.stage() << "_" << op.block();
        return stream;
    }

    int residual() const;
    void setResidual(int newResidual);

    int stage() const;
    void setStage(int newStage);

    int block() const;
    void setBlock(int newBlock);

private:
    int m_residual;
    int m_stage;
    int m_block;
};

/**
 * @brief The Operand class represents an operand for a PISA instruction.
 */
class Operand
{
public:
    Operand() :
        m_location("unassigned"),
        m_bank(-1)
    {
    }

    Operand(const std::string &_location, bool _immediate) :
        m_location(_location),
        m_immediate(_immediate)
    {
    }

    Operand(const std::string &name, int bank) :
        m_bank(bank),
        m_immediate(false)
    {
        setLocation(name);
    }

    Operand(const std::string &location_and_bank)
    {
        std::string location;
        std::string bank;

        std::istringstream splitter(location_and_bank);
        splitter >> std::skipws >> location;
        splitter >> bank;

        setLocation(location);
        if (bank.size() > 2)
        {
            bank   = bank.substr(1, bank.size() - 2);
            m_bank = std::stoi(bank);
        }
        m_immediate = false;
    }

    const std::string &location() const
    {
        return m_location;
    }

    void setLocation(const std::string &newLocation)
    {
        const auto &[root, index] = splitLocation(newLocation);
        m_location_root           = root;
        m_location_index          = index;
        m_location                = root + index;
    }

    int bank() const
    {
        return m_bank;
    }

    void setBank(int newBank)
    {
        m_bank = newBank;
    }

    friend std::ostream &operator<<(std::ostream &stream, const Operand &op)
    {
        stream << op.location();
        if (op.immediate() == false && op.outputBank())
            stream << " (" << op.bank() << ")";

        return stream;
    }

    bool immediate() const;
    void setImmediate(bool newImmediate);

    const std::string &locationRoot() const;
    void setLocationRoot(const std::string &newLocation_root);

    bool outputBank() const;
    void setOutputBank(bool newOutput_bank);

private:
    /**
     * @brief splitLocation
     * @param location
     * Attempts to split the register name into a root and address portion. Does this by reversing V0 logic that always appends poly and rns terms
     * to end of input/register names(but varies depending on if 1 or n outputs)
     */
    static std::pair<std::string, std::string> splitLocation(const std::string &location)
    {
        std::string reg_name = location;
        int count            = std::count(location.begin(), location.end(), '_');
        if (count == 0)
            return std::pair{ location, "" };

        int size = reg_name.size();
        for (int x = 0; x < count; x++)
        {
            size = reg_name.rfind('_', size) - 1;
        }
        size = size + 1;

        return std::pair{ location.substr(0, size),
                          location.substr(size, location.size()) };
    }

    std::string m_location_root;
    std::string m_location_index;
    std::string m_location;
    int m_bank;
    bool m_immediate;
    bool m_output_bank = true;
};

/**
 * @brief The PISAInstruction class represents an instruction in the P-ISA instruction set.
 * It is designed to be able to store all ISA instructions, not all elements are used for every instruction.
 * The exact elements used by each instruction is stored in InstructionDesc.
 */

class PISAInstruction : public ISAInstruction
{

public:
    PISAInstruction(std::string name);
    PISAInstruction(std::string name, InstructionDesc desc);

    Operand &getInputOperand(int n);

    Operand &getOutputOperand(int n);

    void setInputOperand(const Operand &op, int n);

    void setOutputOperand(const Operand &op, int n);

    void addInputOperand(const Operand &op);

    void addOutputOperand(const Operand &op);

    int PMD() const;
    void setPMD(int newPmd_log2);

    const std::string &Name() const;
    void setName(const std::string &newOperation_name);

    int residual() const;
    void setResidual(int newResidual);

    friend std::ostream &operator<<(std::ostream &stream, PISAInstruction instr)
    {
        int input_count  = 0;
        int output_count = 0;
        int element      = 0;
        for (pisa::PARAM_TYPE x : instr.getDescription().params)
        {
            if (element != 0)
                stream << ", ";

            switch (x)
            {
            case pisa::GROUP_ID:
                stream << instr.groupId() << " ";
                break;
            case pisa::STAGE:
                stream << instr.stage() << " ";
                break;
            case pisa::BLOCK:
                stream << instr.block() << " ";
                break;
            case pisa::OP_NAME:
                stream << instr.Name() << " ";
                break;
            case pisa::INPUT_OPERAND:
                stream << instr.getInputOperand(input_count);
                input_count++;
                break;
            case pisa::OUTPUT_OPERAND:
                stream << instr.getOutputOperand(output_count);
                output_count++;
                break;
            case pisa::INPUT_OUTPUT_OPERAND:
                stream << instr.getOutputOperand(output_count);
                input_count++;
                output_count++;
                break;
            case pisa::POLYMOD_DEG_LOG2:
                stream << instr.PMD();
                break;
            case pisa::RESIDUAL:
                stream << instr.residual();
                break;
            case pisa::W_PACKED_PARAM:
                stream << instr.wParam();
                break;
            case pisa::IMMEDIATE:
                stream << instr.getInputOperand(input_count);
                input_count++;
                break;
                // temporary
            case pisa::GALOIS_ELEMENT:
                stream << instr.galois_element();
                input_count++;
                break;
            case pisa::ADDITIONAL_PARAMS:
                break;
            }
            element++;
        }

        return stream;
    }

    int numOutputOperands() const;
    int numInputOperands() const;

    int stage() const;
    void setStage(int newStage);

    int block() const;
    void setBlock(int newBlock);

    const WParam &wParam() const;
    void setWParam(const WParam &newW_param);
    // temporary
    int galois_element() const;
    void setGalois_element(int newGalois_element);

    static std::string operationName();

    const InstructionDesc getDescription() const;
    virtual PISAInstruction *create();

    bool outputBlock() const;
    void setOutputBlock(bool newOutput_block);

    int groupId() const;
    void setGroupId(int newGroup_id);

protected:
    int m_pmd_log2;
    std::string m_operation_name;
    std::vector<Operand> m_input_operands;
    std::vector<Operand> m_output_operands;
    std::vector<int> m_additional_params;
    WParam m_w_param;
    int m_residual;
    int m_group_id;
    int m_stage;

    int m_galois_element;

    int m_block;
    //Specifies if block parameter should be output as part of operand
    bool m_output_block;
    InstructionDesc m_description;
};

} // namespace pisa
