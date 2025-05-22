// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "p_isa_instruction.h"

namespace pisa {
PISAInstruction::PISAInstruction(std::string name) :
    m_operation_name(name)
{
}

PISAInstruction::PISAInstruction(std::string name, InstructionDesc desc) :
    m_operation_name(name),
    m_description(desc)
{
}

Operand &PISAInstruction::getInputOperand(int n)
{
    m_input_operands[n].setOutputBank(m_output_block);
    return m_input_operands[n];
}

Operand &PISAInstruction::getOutputOperand(int n)
{
    m_output_operands[n].setOutputBank(m_output_block);
    return m_output_operands[n];
}

void PISAInstruction::setInputOperand(const Operand &op, int n)
{
    m_input_operands[n] = op;
}

void PISAInstruction::setOutputOperand(const Operand &op, int n)
{
    m_output_operands[n] = op;
}

void PISAInstruction::addInputOperand(const Operand &op)
{
    m_input_operands.push_back(op);
}

void PISAInstruction::addOutputOperand(const Operand &op)
{
    m_output_operands.push_back(op);
}

int PISAInstruction::PMD() const
{
    return m_pmd_log2;
}

void PISAInstruction::setPMD(int newPmd_log2)
{
    m_pmd_log2 = newPmd_log2;
}

const std::string &PISAInstruction::Name() const
{
    return m_operation_name;
}

void PISAInstruction::setName(const std::string &newOperation_name)
{
    m_operation_name = newOperation_name;
}

int PISAInstruction::residual() const
{
    return m_residual;
}

void PISAInstruction::setResidual(int newResidual)
{
    m_residual = newResidual;
}

int PISAInstruction::numOutputOperands() const
{
    return m_output_operands.size();
}

int PISAInstruction::numInputOperands() const
{
    return m_input_operands.size();
}

int PISAInstruction::stage() const
{
    return m_stage;
}

void PISAInstruction::setStage(int newStage)
{
    m_stage = newStage;
}

int PISAInstruction::block() const
{
    return m_block;
}

void PISAInstruction::setBlock(int newBlock)
{
    m_block = newBlock;
}

// temporary
int PISAInstruction::galois_element() const
{
    return m_galois_element;
}

void PISAInstruction::setGalois_element(int newGalois_element)
{
    m_galois_element = newGalois_element;
}

std::string PISAInstruction::operationName()
{
    return std::string("base");
}

const InstructionDesc PISAInstruction::getDescription() const
{
    return m_description;
}

PISAInstruction *PISAInstruction::create()
{
    return new PISAInstruction("none");
}

const WParam &PISAInstruction::wParam() const
{
    return m_w_param;
}

void PISAInstruction::setWParam(const WParam &newW_param)
{
    m_w_param = newW_param;
}

bool PISAInstruction::outputBlock() const
{
    return m_output_block;
}

void PISAInstruction::setOutputBlock(bool newOutput_block)
{
    m_output_block = newOutput_block;
}

int PISAInstruction::groupId() const
{
    return m_group_id;
}

void PISAInstruction::setGroupId(int newGroup_id)
{
    m_group_id = newGroup_id;
}

int WParam::residual() const
{
    return m_residual;
}

void WParam::setResidual(int newResidual)
{
    m_residual = newResidual;
}

int WParam::stage() const
{
    return m_stage;
}

void WParam::setStage(int newStage)
{
    m_stage = newStage;
}

int WParam::block() const
{
    return m_block;
}

void WParam::setBlock(int newBlock)
{
    m_block = newBlock;
}

bool Operand::immediate() const
{
    return m_immediate;
}

void Operand::setImmediate(bool newImmediate)
{
    m_immediate = newImmediate;
}

const std::string &Operand::locationRoot() const
{
    return m_location_root;
}

void Operand::setLocationRoot(const std::string &newLocation_root)
{
    m_location_root = newLocation_root;
    m_location      = m_location_root + m_location_index;
}

bool Operand::outputBank() const
{
    return m_output_bank;
}

void Operand::setOutputBank(bool newOutput_bank)
{
    m_output_bank = newOutput_bank;
}

} // namespace pisa
