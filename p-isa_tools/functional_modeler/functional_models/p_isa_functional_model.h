// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <cmath>
#include <iostream>
#include <limits>
#include <map>
#include <mutex>
#include <string>

#include <common/graph/graph.h>
#include <common/p_isa/p_isa_instructions.h>
#include <functional_modeler/functional_models/p_isa_memory_model.h>
#include <functional_modeler/functional_models/utility_functions.h>
#include <functional_modeler/pisa_runtime/p_isa_instruction_trace.h>

namespace pisa {
template <typename T>
using TwiddleMap = std::unordered_map<std::string, std::vector<std::vector<T>>>;

template <typename T>
class PISAFunctionalModel
{
public:
    PISAFunctionalModel();

    void generate_bit_reverse_table(int N, int ln);

    /**
     * @brief decode: decodes instruction into a specific instance before calling implementation for that instruction.
     * @param instr
     */
    void decode(pisa::PISAInstruction *instr);

    /**
     * @brief montgomeryMul Performs montgomery Mul with uint64_t inputs.
     * @param a
     * @param b
     * @param modulus
     * @param use_mont
     * @return
     */

    T montgomeryMul(T a, T b, T modulus, bool use_mont = true);
    T montgomeryAdd(T a, T b, T modulus, bool use_mont = true);

    /**
     * @brief readOutput Reads the values stored in the output memory locations and returns them as a vector
     * @param instr
     * @return
     */
    std::vector<pisa::MultiRegister<T>> readOutput(pisa::PISAInstruction *instr);

    /**
     * @brief readInput Reads the values stored in the input memory locations and returns them as a vector
     * @param instr
     * @return
     */
    std::vector<pisa::MultiRegister<T>> readInput(pisa::PISAInstruction *instr);

    /**
     *
     * @brief add provides functional implementation of add operation.
     *
     * @details
     *
     */
    void addInstrDecodeExecute(pisa::instruction::Add *instr);
    /**
     * @brief copy provides functional implementation of copy operation.
     *
     * Operation Definition
     * dst(int32) = (src_1(int32))
     */
    void copyInstrDecodeExecute(pisa::instruction::Copy *instr);

    /**
     * @brief sub provides functional implementation of sub operation.
     *
     * Operation Definition
     * dst(int32) = (src_1(int32) - src_2(int32)) % modulus_q
     */
    void subInstrDecodeExecute(pisa::instruction::Sub *instr);

    /**
     * @brief mul provides functional implementation of mul operation.
     *
     * Operation Definition
     * dst(int32) = (src_1(int32)*src_2(int32)) % modulus_q
     */
    void mulInstrDecodeExecute(pisa::instruction::Mul *instr);

    /**
     * @brief muli provides functional implementation of muli operation which multiplies a multiregister elementwise by a scalar immediate value
     *
     * Operation Definition
     * dst(pisa::MultiRegister<T>32) = (src_1(pisa::MultiRegister<T>32)*immediate) % modulus_q
     */
    void muliInstrDecodeExecute(pisa::instruction::Muli *instr);

    /**
     * @brief mac provides functional implementation of mac operation.
     *
     * Operation Definition
     * dst(int32) = (dst(int32) + src_1(int32)*src_2(int32)) % modulus_q
     */
    void macInstrDecodeExecute(pisa::instruction::Mac *instr);

    /**
     * @brief maci provides functional implementation of maci operation.
     *
     * Operation Definition
     * dst(int32) = (dst(int32) + src_1(int32)*imm(int32)) % modulus_q
     */
    void maciInstrDecodeExecute(pisa::instruction::Maci *instr);

    /**
     * @brief iNTT provides functional implementation of iNTT operation.
     * @todo This all needs to be verified
     * Operation Definition
     * dst0 = src0;
     * dst1 = src1;
     */
    void iNttInstrDecodeExecute(pisa::instruction::Intt *instr);

    /**
     * @brief NTT provides functional implementation of NTT operation.
     * @todo This all needs to be verified
     * Operation Definition
     *
     */
    void nttInstrDecodeExecute(pisa::instruction::Ntt *instr);

    std::vector<T> getModulusChain() const;
    void setModulusChain(std::vector<T> new_modulus_chain);

    /**
     * @brief getMatching3ParamRegisterNames will match 2 param names in form of <name>_<index0>_<index1> with matching 3 param names of form <name>_<index0>_<index1>_<index2
     * @param register_2_param_name
     * @return
     */
    std::vector<std::string> getMatching3ParamRegisterNames(std::string register_2_param_name);

    const std::vector<pisa::PISAInstructionTrace<T>> &executionTrace() const;
    void enableExecutionTrace();
    void stopExecutionTrace();

    const std::vector<std::vector<T>> &getTwiddleNtt() const;
    void setTwiddleNtt(const std::vector<std::vector<T>> &newTwiddle_ntt);

    const TwiddleMap<T> &getTwiddleIntt() const;
    void setTwiddleIntt(const TwiddleMap<T> &newTwiddle_intt);

    uint getMultiRegisterWidth() const;

    PISAMemoryModel<T> &getMemory();
    void setMemory(const PISAMemoryModel<T> &newMemory);

    /**
     * @brief dumpMemoryToStream outputs all values currently stored in the devices memory and any global context memory values.
     * @param output_stream An output stream object to which to write memory values
     */
    void dumpMemoryToStream(std::ostream &output_stream);
    void dumpMemoryToStream(std::ostream &output_stream, std::vector<std::string> addresses);
    /**
     * @brief readMemoryFromStream Accepts a memory dump in csv format and sets all memory values to provided values.
     * @param input_stream
     */
    void readMemoryFromStream(std::istream &input_stream);

private:
    void createStartTable(int increment);

    std::vector<uint32_t> m_bit_reverse_table;
    /* Memory model used by functional modeler */
    PISAMemoryModel<T> m_memory;

    /* Context parameters */
    std::vector<T> m_modulus_chain;
    std::vector<std::vector<T>> m_twiddle_ntt;
    TwiddleMap<T> m_twiddle_intt;
    const uint m_multi_register_width = 8192;

    bool m_montgomery_enabled        = true;
    bool m_debug_information_enabled = false;
    bool m_trace_execution           = false;
    std::vector<int> m_start_table;

    std::vector<pisa::PISAInstructionTrace<T>> m_execution_trace;
};

template <typename T>
PISAFunctionalModel<T>::PISAFunctionalModel()
{
    m_memory.setRegisterWidth(m_multi_register_width);
}

template <typename T>
void PISAFunctionalModel<T>::generate_bit_reverse_table(int N, int ln)
{
    for (uint x = 0; x < N; x++)
    {
        m_bit_reverse_table.push_back(pisa::utility::reverseBits<T>(x, ln - 1));
    }
}

template <typename T>
void PISAFunctionalModel<T>::decode(pisa::PISAInstruction *instr)
{
    try
    {

        if (this->m_trace_execution)
        {
            pisa::PISAInstructionTrace<T> instruction_trace;
            instruction_trace.setInstruction(instr);
            m_execution_trace.push_back(instruction_trace);

            //Grab inputs
            std::vector<pisa::MultiRegister<T>> inputs;
            for (int x = 0; x < m_execution_trace.back().instruction()->numInputOperands(); x++)
            {
                inputs.push_back(m_memory.copy(instr->getInputOperand(x).location()));
            }
            m_execution_trace.back().setExecutionInputs(inputs);
        }

        if (instr->Name() == pisa::instruction::Add::baseName)
        {
            addInstrDecodeExecute(static_cast<pisa::instruction::Add *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Sub::baseName)
        {
            subInstrDecodeExecute(static_cast<pisa::instruction::Sub *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Mul::baseName)
        {
            mulInstrDecodeExecute(static_cast<pisa::instruction::Mul *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Muli::baseName)
        {
            muliInstrDecodeExecute(static_cast<pisa::instruction::Muli *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Mac::baseName)
        {
            macInstrDecodeExecute(static_cast<pisa::instruction::Mac *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Maci::baseName)
        {
            maciInstrDecodeExecute(static_cast<pisa::instruction::Maci *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Intt::baseName)
        {
            iNttInstrDecodeExecute(static_cast<pisa::instruction::Intt *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Ntt::baseName)
        {
            nttInstrDecodeExecute(static_cast<pisa::instruction::Ntt *>(instr));
        }
        else if (instr->Name() == pisa::instruction::Copy::baseName)
        {
            copyInstrDecodeExecute(static_cast<pisa::instruction::Copy *>(instr));
        }
        else
        {
            throw std::runtime_error("Failed to decode " + instr->Name());
        }

        if (this->m_trace_execution)
        {
            //Grab results
            std::vector<pisa::MultiRegister<T>> results;
            for (int x = 0; x < m_execution_trace.back().instruction()->numOutputOperands(); x++)
            {
                results.push_back(m_memory.copy(instr->getOutputOperand(x).location()));
            }
            m_execution_trace.back().setExecutionResult(results);
        }
    }
    catch (std::runtime_error err)
    {
        std::cout << "Failed to decode instr: " << err.what() << std::endl;
        throw;
    }
}

template <typename T>
T PISAFunctionalModel<T>::montgomeryMul(T a, T b, T modulus, bool use_mont)
{
    if (use_mont)
    {
        uint64_t u = static_cast<uint64_t>(a) * static_cast<uint64_t>(b);
        uint64_t k = modulus - 2;
        uint64_t t = u & std::numeric_limits<uint>::max();
        uint64_t m = (t * k) & std::numeric_limits<uint>::max();
        u += m * modulus;
        u >>= 32;
        u = u - (u >= modulus) * modulus;

        return u;
    }
    else
    {
        return a * b % modulus;
    }
}

template <typename T>
T PISAFunctionalModel<T>::montgomeryAdd(T a, T b, T modulus, bool use_mont)
{
    if (use_mont)
    {
        uint64_t u = a + b;
#ifdef DEBUG
        if (u >= 2 * modulus)
            throw std::runtime_error("Value out of bounds");
#endif
        if (u < modulus)
        {
            u = u;
        }
        else
        {
            u = u - modulus;
        }
        return u;
    }
    else
    {
        return a + b % modulus;
    }
}

template <typename T>
std::vector<pisa::MultiRegister<T>> PISAFunctionalModel<T>::readOutput(pisa::PISAInstruction *instr)
{
    std::vector<pisa::MultiRegister<T>> results;
    for (int x = 0; x < instr->numOutputOperands(); x++)
    {
        auto result = instr->getOutputOperand(x);
        results.push_back(m_memory.readMemory(result.location()));
    }
    return results;
}

template <typename T>
std::vector<pisa::MultiRegister<T>> PISAFunctionalModel<T>::readInput(pisa::PISAInstruction *instr)
{
    std::vector<pisa::MultiRegister<T>> results;
    for (int x = 0; x < instr->numInputOperands(); x++)
    {
        auto result = instr->getInputOperand(x);
        results.push_back(m_memory.readMemory(result.location()));
    }
    return results;
}

template <typename T>
void PISAFunctionalModel<T>::addInstrDecodeExecute(pisa::instruction::Add *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
    pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(1).location()];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];
#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        dst[x] = montgomeryAdd(src_1[x], src_2[x], modulus, true);
    }

    return;
}

template <typename T>
void PISAFunctionalModel<T>::copyInstrDecodeExecute(pisa::instruction::Copy *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];

    dst = src_1;

    return;
}

template <typename T>
void PISAFunctionalModel<T>::subInstrDecodeExecute(pisa::instruction::Sub *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
    pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(1).location()];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];

#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        auto z = modulus - src_2[x];
        if (z >= modulus)
            z -= modulus;
        dst[x] = montgomeryAdd(src_1[x], z, modulus, true);
    }

    return;
}

template <typename T>
void PISAFunctionalModel<T>::mulInstrDecodeExecute(pisa::instruction::Mul *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
    pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(1).location()];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];
#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        dst[x] = montgomeryMul(src_1[x], src_2[x], modulus, true);
    }
}

template <typename T>
void PISAFunctionalModel<T>::muliInstrDecodeExecute(pisa::instruction::Muli *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
    T &src_2                      = m_memory[instr->getInputOperand(1).location()][0];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];
#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        dst[x] = montgomeryMul(src_1[x], src_2, modulus, true);
    }
}

template <typename T>
void PISAFunctionalModel<T>::macInstrDecodeExecute(pisa::instruction::Mac *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &accum = m_memory[instr->getInputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(1).location()];
    pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(2).location()];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];
#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        auto tmp = montgomeryMul(src_1[x], src_2[x], modulus, true);
        dst[x]   = montgomeryAdd(accum[x], tmp, modulus, true);
    }
}

template <typename T>
void PISAFunctionalModel<T>::maciInstrDecodeExecute(pisa::instruction::Maci *instr)
{
    //Decode
    pisa::MultiRegister<T> &dst   = m_memory[instr->getOutputOperand(0).location()];
    pisa::MultiRegister<T> &accum = m_memory[instr->getInputOperand(0).location()];
    pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(1).location()];
    T &src_2                      = m_memory[instr->getInputOperand(2).location()][0];

    //Exec
    const auto modulus = m_modulus_chain[instr->residual()];
#pragma omp parallel for
    for (int x = 0; x < m_multi_register_width; x++)
    {
        auto tmp = montgomeryMul(src_1[x], src_2, modulus, true);
        dst[x]   = montgomeryAdd(accum[x], tmp, modulus, true);
    }
}

template <typename T>
void PISAFunctionalModel<T>::iNttInstrDecodeExecute(pisa::instruction::Intt *instr)
{
    try
    {
        //Decode
        pisa::MultiRegister<T> &dst_0 = m_memory[instr->getOutputOperand(0).location()];
        pisa::MultiRegister<T> &dst_1 = m_memory[instr->getOutputOperand(1).location()];
        pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
        pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(1).location()];

        const int lN              = instr->PMD();
        const int N               = pow(2, lN);
        const int half_N          = N >> 1;
        const int block_size      = src_1.size() * 2;
        const int half_block      = src_1.size();
        const int starting_offset = block_size * instr->wParam().block();
        const auto modulus        = m_modulus_chain[instr->wParam().residual()];
        const auto stage          = instr->wParam().stage();
        // TODO: discuss how to handle twiddle map key values - currently just  "{ge}", it could only be the ge value instead..
        const std::string ge  = std::to_string(instr->galois_element());
        const int block_count = lN - 14;
        const int increment   = pow(2, block_count);

        const int slice_size = half_N / increment;
        const int start      = instr->wParam().block() * slice_size;
        const int end        = start + slice_size;

        if (m_bit_reverse_table.size() == 0)
        {
            generate_bit_reverse_table(N, lN);
        }

#pragma omp parallel for
        for (uint32_t i = start; i < end; i += 1)
        {
            auto j = m_bit_reverse_table[i]; //

            int in0  = i % half_block;
            int in1  = ((i + half_N) % half_block) + half_block;
            int out0 = 2 * i % block_size;
            int out1 = (2 * i + 1) % block_size; //Reads from input

            int sp = lN - 1 - stage;
            int k  = (j >> sp) << sp;

            //Resolve input and output locations based on index and spread across two inputs)
            T Xin_0   = in0 < half_block ? (src_1.data()[in0]) : (src_2.data()[in0 - half_block]);
            T Xin_1   = in1 < half_block ? (src_1.data()[in1]) : (src_2.data()[in1 - half_block]);
            T &Xout_0 = out0 < half_block ? (dst_0.data()[out0]) : (dst_1.data()[out0 - half_block]);
            T &Xout_1 = out1 < half_block ? (dst_0.data()[out1]) : (dst_1.data()[out1 - half_block]);

            T t0 = Xin_0;
            T t1 = montgomeryMul(Xin_1, m_twiddle_intt.at(ge)[instr->wParam().residual()][k], modulus, true); // Need montgomery mul single op
            T t2 = modulus - t1;

            Xout_0 = montgomeryAdd(t0, t1, modulus, true);
            Xout_1 = montgomeryAdd(t0, t2, modulus, true);
        }

        return;
    }
    catch (std::runtime_error err)
    {
        std::cout << "INtt runtime error:" << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        throw;
    }
}

template <typename T>
void PISAFunctionalModel<T>::nttInstrDecodeExecute(pisa::instruction::Ntt *instr)
{
    try
    {
        //Decode
        pisa::MultiRegister<T> &dst_0 = m_memory[instr->getOutputOperand(0).location()];
        pisa::MultiRegister<T> &dst_1 = m_memory[instr->getOutputOperand(1).location()];
        pisa::MultiRegister<T> &src_1 = m_memory[instr->getInputOperand(0).location()];
        pisa::MultiRegister<T> &src_2 = m_memory[instr->getInputOperand(1).location()];

        const int lN              = instr->PMD();
        const int N               = pow(2, lN);
        const int half_N          = N >> 1;
        const int block_size      = src_1.size() * 2;
        const int half_block      = src_1.size();
        const int starting_offset = block_size * instr->wParam().block();

        const int block_count = lN - 14;
        const int increment   = pow(2, block_count);

        if (m_start_table.size() == 0)
        {
            createStartTable(increment);
        }

        const int start     = m_start_table[instr->wParam().block()];
        const auto residual = instr->wParam().residual();
        const auto modulus  = m_modulus_chain[residual];
        const auto stage    = instr->wParam().stage();

        //Compute the bit reversal table if needed
        if (m_bit_reverse_table.size() == 0)
        {
            generate_bit_reverse_table(N, lN);
        }

#pragma omp parallel for
        for (uint32_t i = start; i < half_N; i += increment)
        {
            auto j = m_bit_reverse_table[i]; // Look up precomputed bit_reverse values

            int in0  = (2 * j) % block_size;
            int in1  = (2 * j + 1) % block_size;
            int out0 = j % half_block;
            int out1 = ((j + half_N) % half_block) + half_block;

            int sp = lN - 1 - stage;
            int k  = (j >> sp) << sp;

            //Resolve input and output locations based on index and spread across two inputs)
            T Xin_0   = in0 < half_block ? (src_1.data()[in0]) : (src_2.data()[in0 - half_block]);
            T Xin_1   = in1 < half_block ? (src_1.data()[in1]) : (src_2.data()[in1 - half_block]);
            T &Xout_0 = out0 < half_block ? (dst_0.data()[out0]) : (dst_1.data()[out0 - half_block]);
            T &Xout_1 = out1 < half_block ? (dst_0.data()[out1]) : (dst_1.data()[out1 - half_block]);

            T t0 = Xin_0;
            T t1 = 0;
            if (stage == 0)
            {
                t1 = Xin_1;
            }
            else
            {
                t1 = montgomeryMul(Xin_1, m_twiddle_ntt[residual][k], modulus, true); // Need montgomery mul single op
            }
            T t2 = modulus - t1;

            Xout_0 = montgomeryAdd(t0, t1, modulus, true);
            Xout_1 = montgomeryAdd(t0, t2, modulus, true);
        }

        return;
    }
    catch (std::runtime_error err)
    {
        std::cout << "Ntt runtime error:" << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        throw;
    }
}

template <typename T>
std::vector<T> PISAFunctionalModel<T>::getModulusChain() const
{
    return m_modulus_chain;
}

template <typename T>
void PISAFunctionalModel<T>::setModulusChain(std::vector<T> new_modulus_chain)
{
    m_modulus_chain = new_modulus_chain;
}

template <typename T>
std::vector<std::string> PISAFunctionalModel<T>::getMatching3ParamRegisterNames(std::string register_2_param_name)
{
    std::vector<std::string> register_names;
    int index_count = std::count(register_2_param_name.begin(), register_2_param_name.end(), '_');
    for (auto mem : m_memory.registers())
    {
        std::string reg_name = mem.first;
        int size             = reg_name.rfind('_', reg_name.size());

        auto short_name = reg_name.substr(0, size);
        if (short_name == register_2_param_name)
        {
            register_names.push_back(mem.first);
        }
    }
    return register_names;
}

template <typename T>
const std::vector<pisa::PISAInstructionTrace<T>> &PISAFunctionalModel<T>::executionTrace() const
{
    return m_execution_trace;
}

template <typename T>
void PISAFunctionalModel<T>::enableExecutionTrace()
{
    m_execution_trace.clear();
    m_trace_execution = true;
}

template <typename T>
void PISAFunctionalModel<T>::stopExecutionTrace()
{
    m_trace_execution = false;
}

template <typename T>
void PISAFunctionalModel<T>::createStartTable(int increment)
{
    for (int x = 0; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //8
    for (int x = 4; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //10
    for (int x = 2; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //12
    for (int x = 6; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //14

    for (int x = 1; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //9
    for (int x = 5; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //11
    for (int x = 3; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
    //13
    for (int x = 7; x < increment; x += 8)
    {
        m_start_table.push_back(x);
    }
}

template <typename T>
PISAMemoryModel<T> &PISAFunctionalModel<T>::getMemory()
{
    return m_memory;
}

template <typename T>
void PISAFunctionalModel<T>::setMemory(const PISAMemoryModel<T> &newMemory)
{
    m_memory = newMemory;
}

template <typename T>
void PISAFunctionalModel<T>::dumpMemoryToStream(std::ostream &output_stream)
{
    int ntt_index = 0;
    for (auto x : m_twiddle_ntt)
    {
        output_stream << "ntt," << ntt_index;
        ntt_index++;
        for (auto y : x)
        {
            output_stream << "," << y;
        }
        output_stream << std::endl;
    }
    int intt_index = 0;
    for (auto intt_map_item : m_twiddle_intt)
    {
        intt_index = 0;
        for (auto x : intt_map_item.second)
        {
            output_stream << "intt," << intt_map_item.first << "," << intt_index;
            intt_index++;
            for (auto y : x)
            {
                output_stream << "," << y;
            }
            output_stream << std::endl;
        }
    }

    output_stream << "modulus_chain";
    for (auto val : m_modulus_chain)
    {
        output_stream << "," << val;
    }
    output_stream << std::endl;

    //Write out all registers
    for (auto mem_register : m_memory.registers())
    {
        output_stream << "memory," << mem_register.first;
        for (auto val : mem_register.second->data())
        {
            output_stream << "," << val;
        }
        output_stream << std::endl;
    }
}

template <typename T>
void PISAFunctionalModel<T>::dumpMemoryToStream(std::ostream &output_stream, std::vector<std::string> addresses)
{
    //Write out all registers identified by addresses
    for (auto address : addresses)
    {
        auto mem_register = m_memory[address];
        output_stream << "memory," << address;
        for (auto val : mem_register.data())
        {
            output_stream << "," << val;
        }
        output_stream << std::endl;
    }
}

template <typename T>
void PISAFunctionalModel<T>::readMemoryFromStream(std::istream &input_stream)
{
    try
    {
        std::string current_line;
        while (std::getline(input_stream, current_line))
        {
            std::vector<std::string> components;
            std::istringstream current_line_ss(current_line);

            std::string component;
            while (std::getline(current_line_ss, component, ','))
            {
                if (component != "\r" && component != "")
                    components.push_back(std::move(component));
            }
            if (components[0] == "memory")
            {
                std::vector<T> values;
                std::transform((components.begin() + 2), components.end(), std::back_inserter(values), [this](auto s) {
                    return std::stoi(s);
                });
                m_memory[components[1]].setData(values);
            }
            if (components[0] == "modulus_chain")
            {
                std::vector<T> values;
                std::transform((components.begin() + 1), components.end(), std::back_inserter(values), [this](auto s) {
                    return std::stoi(s);
                });
                this->setModulusChain(values);
            }
            if (components[0] == "ntt")
            {
                if (m_twiddle_ntt.size() < std::stoi(components[1]))
                {
                    m_twiddle_ntt.resize(std::stoi(components[1]));
                }

                std::vector<T> values;
                std::transform((components.begin() + 2), components.end(), std::back_inserter(values), [this](auto s) {
                    return std::stoi(s);
                });

                m_twiddle_ntt[std::stoi(components[1])] = values;
            }
            if (components[0] == "intt")
            {
                if (m_twiddle_intt.count(components[1]) == 0)
                {
                    m_twiddle_intt[components[1]];
                }
                auto intt_values = m_twiddle_intt[components[1]];
                if (intt_values.size() < std::stoi(components[2]))
                {
                    intt_values.resize(std::stoi(components[2]));
                }

                std::vector<T> values;
                std::transform((components.begin() + 3), components.end(), std::back_inserter(values), [this](auto s) {
                    return std::stoi(s);
                });
                intt_values[std::stoi(components[2])] = values;
            }
        }
    }
    catch (...)
    {
        throw std::runtime_error("Encountered error while reading memory from memory file");
    }
}

template <typename T>
uint PISAFunctionalModel<T>::getMultiRegisterWidth() const
{
    return m_multi_register_width;
}

template <typename T>
const TwiddleMap<T> &PISAFunctionalModel<T>::getTwiddleIntt() const
{
    return m_twiddle_intt;
}

template <typename T>
void PISAFunctionalModel<T>::setTwiddleIntt(const TwiddleMap<T> &newTwiddle_intt)
{
    m_twiddle_intt = newTwiddle_intt;
}

template <typename T>
const std::vector<std::vector<T>> &PISAFunctionalModel<T>::getTwiddleNtt() const
{
    return m_twiddle_ntt;
}

template <typename T>
void PISAFunctionalModel<T>::setTwiddleNtt(const std::vector<std::vector<T>> &newTwiddle_ntt)
{
    m_twiddle_ntt = newTwiddle_ntt;
}

} // namespace pisa
