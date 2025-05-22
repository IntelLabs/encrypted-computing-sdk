// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <fstream>
#include <iostream>
#include <vector>

#include <common/p_isa/p_isa.h>
#include <functional_modeler/functional_models/p_isa_functional_model.h>

/**
 * @class PISAProgramRuntime
 * @brief The PISAProgramRuntime class provides an interface to a PISA Functional model with functions for setting and getting
 * memory and scheduling p-isa instruction execution.
 */
template <typename T>
class PISAProgramRuntime
{
public:
    PISAProgramRuntime() = default;

    /* Memory accessor functions */
    std::vector<T> getModulusChain();
    /**
     * @brief get2ParamMemoryFromDeviceMemory takes a string of form label_ringsize_RNS and returns a pair with all of the device terms reassembled.
     * @param memory_2_param_root
     * @return
     */
    std::pair<std::string, std::vector<T>> getParamMemoryFromMultiRegisterDeviceMemory(std::string memory_2_param_root);
    void getMemory(std::vector<std::pair<std::string, pisa::MultiRegister<T>>> &memory_locations);

    /* Memory Set Functions */
    void setModulusChain(std::vector<T> modulus_chain);
    void setMemory(std::vector<std::pair<std::string, pisa::MultiRegister<T>>> memory_values);
    void setMemory(std::pair<std::string, pisa::MultiRegister<T>> memory_value);
    /**
     * @brief set2ParamMemoryToDeviceMemory takes a pair containing a memory address in 2 parameter form label_ringsize_RNS
     * and maps it to device memory in label_ringsize_RNS_slice format.
     * @param trace_memory_map
     */
    void setParamMemoryToMultiRegisterDeviceMemory(std::pair<std::string, std::vector<T>> trace_memory_map);
    void setParamMemoryToMultiRegisterDeviceMemory(std::vector<std::pair<std::string, std::vector<T>>> trace_memory_map);
    void setImmediateToMultiRegisterDeviceMemory(std::pair<std::string, std::vector<T>> trace_memory_map);
    void setImmediatesToMultiRegisterDeviceMemory(std::vector<std::pair<std::string, std::vector<T>>> trace_memory_map);
    void setNTTTwiddleFactors(std::vector<std::vector<T>> ntt_tw);
    void setINTTTwiddleFactors(pisa::TwiddleMap<T> intt_tw);

    /* Code Execution functions */
    void executeProgram(const std::vector<pisa::PISAInstruction *> &instructions);
    void executeProgram(std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> input_layers);

    void executeInstruction(pisa::PISAInstruction *instruction);

    const pisa::PISAFunctionalModel<T> &model() const;
    void setModel(const pisa::PISAFunctionalModel<T> &newModel);

    bool getDebugMode() const;
    void setDebugMode(bool newDebug_information_enabled);

    void dumpDeviceMemory(std::ostream &output_stream);
    void dumpDeviceMemory(std::ostream &output_stream, std::vector<std::string> addresses);
    void setDeviceMemory(std::istream &input_stream);

private:
    pisa::PISAFunctionalModel<T> m_model;
    bool m_debug_mode = false;
};

//// --------Begin Implementations ----------////
template <typename T>
std::vector<T> PISAProgramRuntime<T>::getModulusChain()
{
    return m_model.getModulusChain();
}

template <typename T>
void PISAProgramRuntime<T>::executeProgram(const std::vector<pisa::PISAInstruction *> &instructions)
{
    try
    {
        if (m_debug_mode)
        {
            m_model.enableExecutionTrace();
        }

        for (const auto &instruction : instructions)
        {
            executeInstruction(instruction);
        }

        if (m_debug_mode)
        {
            m_model.stopExecutionTrace();

            auto trace = m_model.executionTrace();
            for (auto instr : trace)
            {
                instr.printInstructionTrace();
            }
        }
    }
    catch (std::runtime_error err)
    {
        if (m_debug_mode)
        {
            std::cout << err.what() << " Dumping execution log **BEGIN**" << std::endl;
            m_model.stopExecutionTrace();

            auto trace = m_model.executionTrace();
            for (auto instr : trace)
            {
                instr.printInstructionTrace();
            }
            std::cout << "Execution log dump **FINISHED**" << std::endl;
            throw;
        }
        else
        {
            throw;
        }
    }
}

template <typename T>
void PISAProgramRuntime<T>::executeProgram(std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> input_layers)
{
    for (auto &layer : input_layers)
    {
#pragma omp parallel for
        for (const auto &instruction : layer)
        {
            executeInstruction(instruction.GetDat().instruction);
        }
    }
}

template <typename T>
void PISAProgramRuntime<T>::executeInstruction(pisa::PISAInstruction *instruction)
{
    m_model.decode(instruction);
}

template <typename T>
void PISAProgramRuntime<T>::setMemory(std::vector<std::pair<std::string, pisa::MultiRegister<T>>> memory_values)
{
    for (const auto &[k, v] : memory_values)
    {
        m_model.getMemory().writeMemory(k, v);
    }
}

template <typename T>
void PISAProgramRuntime<T>::setMemory(std::pair<std::string, pisa::MultiRegister<T>> memory_value)
{
    m_model.getMemory().writeMemory(memory_value.first, memory_value.second);
}

template <typename T>
void PISAProgramRuntime<T>::setParamMemoryToMultiRegisterDeviceMemory(std::pair<std::string, std::vector<T>> trace_memory_map)
{
    try
    {
        if (trace_memory_map.second.size() % m_model.getMultiRegisterWidth() != 0)
        {
            throw std::runtime_error("Input size not a multiple of multi_register size, mapping undefined");
        }

        uint slice_count = trace_memory_map.second.size() / m_model.getMultiRegisterWidth();
        for (int x = 0; x < slice_count; x++)
        {
            pisa::MultiRegister<T> mem_slice(m_model.getMultiRegisterWidth());
            for (int a = 0; a < m_model.getMultiRegisterWidth(); a++)
            {
                mem_slice[a] = trace_memory_map.second[m_model.getMultiRegisterWidth() * x + a];
            }
            std::string memory_address = trace_memory_map.first + "_" + std::to_string(x);
            setMemory(std::pair<std::string, pisa::MultiRegister<T>>(memory_address, mem_slice));
        }
    }
    catch (...)
    {
        throw;
    }
}

template <typename T>
void PISAProgramRuntime<T>::setParamMemoryToMultiRegisterDeviceMemory(std::vector<std::pair<std::string, std::vector<T>>> trace_memory_map)
{
    try
    {
        for (auto a : trace_memory_map)
        {
            setParamMemoryToMultiRegisterDeviceMemory(a);
        }
    }
    catch (...)
    {
        std::cout << "Unknown error while setting device memory" << std::endl;
    }
}

template <typename T>
void PISAProgramRuntime<T>::setImmediateToMultiRegisterDeviceMemory(std::pair<std::string, std::vector<T>> trace_memory_map)
{
    try
    {
        pisa::MultiRegister<T> mem_slice(1);
        for (int a = 0; a < 1; a++)
        {
            mem_slice[a] = trace_memory_map.second[a];
        }

        setMemory(std::pair<std::string, pisa::MultiRegister<T>>(trace_memory_map.first, mem_slice));
    }
    catch (...)
    {
        throw;
    }
}

template <typename T>
void PISAProgramRuntime<T>::setImmediatesToMultiRegisterDeviceMemory(std::vector<std::pair<std::string, std::vector<T>>> trace_memory_map)
{
    for (const auto &a : trace_memory_map)
    {
        setImmediateToMultiRegisterDeviceMemory(a);
    }
}

template <typename T>
std::pair<std::string, std::vector<T>> PISAProgramRuntime<T>::getParamMemoryFromMultiRegisterDeviceMemory(std::string memory_2_param_root)
{
    try
    {
        std::pair<std::string, std::vector<T>> return_value;
        return_value.first = memory_2_param_root;

        std::vector<std::string> register_names_3_param = m_model.getMatching3ParamRegisterNames(memory_2_param_root);
        std::vector<std::pair<std::string, int>> indexed_list;
        int start = memory_2_param_root.length() + 1;

        for (auto a : register_names_3_param)
        {
            auto index = std::stoi(a.substr(start, a.length() - start));
            indexed_list.push_back(std::pair<std::string, int>(a, index));
        }

        std::sort(indexed_list.begin(), indexed_list.end(),
                  [](const std::pair<std::string, int> &lhs, const std::pair<std::string, int> &rhs) {
                      return lhs.second < rhs.second;
                  });
        std::vector<T> combined_values;
        for (auto a : indexed_list)
        {
            auto memory = m_model.getMemory().readMemory(a.first);
            for (auto &val : memory.data())
            {
                combined_values.push_back(val);
            }
        }
        return_value.second = combined_values;
        return return_value;
    }
    catch (...)
    {
        std::cout << "Error while retrieving device memory" << std::endl;
        throw;
    }
}

template <typename T>
void PISAProgramRuntime<T>::getMemory(std::vector<std::pair<std::string, pisa::MultiRegister<T>>> &memory_locations)
{
    for (auto &a : memory_locations)
    {
        a.second = m_model.getMemory().readMemory(a.first);
    }
}

template <typename T>
void PISAProgramRuntime<T>::setModulusChain(std::vector<T> modulus_chain)
{
    m_model.setModulusChain(modulus_chain);
}

template <typename T>
void PISAProgramRuntime<T>::setNTTTwiddleFactors(std::vector<std::vector<T>> ntt_tw)
{
    m_model.setTwiddleNtt(ntt_tw);
}

template <typename T>
void PISAProgramRuntime<T>::setINTTTwiddleFactors(pisa::TwiddleMap<T> intt_tw)
{
    m_model.setTwiddleIntt(intt_tw);
}

template <typename T>
const pisa::PISAFunctionalModel<T> &PISAProgramRuntime<T>::model() const
{
    return m_model;
}

template <typename T>
void PISAProgramRuntime<T>::setModel(const pisa::PISAFunctionalModel<T> &newModel)
{
    m_model = newModel;
}

template <typename T>
bool PISAProgramRuntime<T>::getDebugMode() const
{
    return m_debug_mode;
}

template <typename T>
void PISAProgramRuntime<T>::setDebugMode(bool newDebug_information_enabled)
{
    m_debug_mode = newDebug_information_enabled;
}

template <typename T>
void PISAProgramRuntime<T>::dumpDeviceMemory(std::ostream &output_stream)
{
    m_model.dumpMemoryToStream(output_stream);
}

template <typename T>
void PISAProgramRuntime<T>::dumpDeviceMemory(std::ostream &output_stream, std::vector<std::string> addresses)
{
    m_model.dumpMemoryToStream(output_stream, addresses);
}

template <typename T>
void PISAProgramRuntime<T>::setDeviceMemory(std::istream &input_stream)
{
    m_model.readMemoryFromStream(input_stream);
}
