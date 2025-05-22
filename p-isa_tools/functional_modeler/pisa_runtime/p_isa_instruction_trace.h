// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "common/p_isa/p_isa_instruction.h"
#include "functional_modeler/functional_models/multiregister.h"

namespace pisa {
template <typename T>
class PISAInstructionTrace
{
public:
    PISAInstructionTrace() {}
    PISAInstructionTrace(std::shared_ptr<PISAInstruction> instr, std::vector<MultiRegister<T>> inputs, std::vector<MultiRegister<T>> outputs);
    const std::vector<MultiRegister<T>> &executionResult() const;
    void setExecutionResult(const std::vector<MultiRegister<T>> &newExecution_result)
    {
        m_execution_result = newExecution_result;
    }

    const std::vector<MultiRegister<T>> &executionInputs() const;
    void setExecutionInputs(const std::vector<MultiRegister<T>> &newExecution_inputs)
    {
        m_execution_inputs = newExecution_inputs;
    }

    std::string outLabel()
    {
        std::ostringstream label_stream;
        auto inputs = executionInputs();
        for (auto &v : inputs)
        {
            label_stream << v.toString() << " , ";
        }
        label_stream << '\n';
        auto results = executionResult();
        for (auto &v : results)
        {
            label_stream << v.toString() << " , ";
        }
        return label_stream.str();
    }

    void printInstructionTrace(int max_values = 10)
    {
        std::cout << "Instruction label: " << m_instruction->Name() << std::endl;
        std::cout << "Inputs:" << std::endl;
        for (int x = 0; x < m_instruction->numInputOperands(); x++)
        {
            std::cout << m_instruction->getInputOperand(x).location() << " : ";
            for (int i = 0; x < m_execution_inputs.size() && i < m_execution_inputs[x].size() && i < max_values; i++)
            {
                std::cout << m_execution_inputs[x][i] << ", ";
            }
            std::cout << std::endl;
        }
        std::cout << "Outputs: " << std::endl;
        for (int x = 0; x < m_instruction->numOutputOperands(); x++)
        {
            std::cout << m_instruction->getOutputOperand(x).location() << " :";
            for (int i = 0; i < x < m_execution_result.size() && m_execution_result[x].size() && i < max_values; i++)
            {
                std::cout << m_execution_result[x][i] << ", ";
            }
            std::cout << std::endl;
        }
        std::cout << std::endl
                  << std::endl;
    }

    const std::shared_ptr<PISAInstruction> &instruction() const
    {
        return m_instruction;
    }
    void setInstruction(const std::shared_ptr<PISAInstruction> &newInstruction)
    {
        m_instruction = newInstruction;
    }
    void setInstruction(pisa::PISAInstruction *instr)
    {
        setInstruction(std::make_shared<PISAInstruction>(*instr));
    }

private:
    std::shared_ptr<PISAInstruction> m_instruction;
    std::vector<MultiRegister<T>> m_execution_inputs;
    std::vector<MultiRegister<T>> m_execution_result;
};
} // namespace pisa
