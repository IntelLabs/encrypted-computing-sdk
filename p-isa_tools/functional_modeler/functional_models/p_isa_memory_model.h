
// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <memory>
#include <mutex>

#include "functional_modeler/functional_models/multiregister.h"
#include <common/graph/graph.h>
#include <common/p_isa/p_isa_instructions.h>

namespace pisa {

template <typename T>
class PISAMemoryModel
{
public:
    pisa::MultiRegister<T> &readMemory(std::string location);
    void writeMemory(std::string location, pisa::MultiRegister<T> value);

    pisa::MultiRegister<T> &reference(std::string location);
    pisa::MultiRegister<T> &operator[](std::string location);
    pisa::MultiRegister<T> copy(std::string location);

    int registerWidth() const;
    void setRegisterWidth(int newRegister_width);

    const std::unordered_map<std::string, pisa::MultiRegister<T> *> &registers() const;

private:
    std::unordered_map<std::string, pisa::MultiRegister<T> *> m_registers;
    int m_register_width;
    std::mutex m_parallel_guard;
};

template <typename T>
pisa::MultiRegister<T> &PISAMemoryModel<T>::readMemory(std::string location)
{
    //const std::lock_guard<std::mutex> lock(parallel_guard);
    if (m_registers.count(location) == 0)
    {
        m_registers[location] = new pisa::MultiRegister<T>();
    }

    pisa::MultiRegister<T> *mem = m_registers[location];
    return *mem;
}

template <typename T>
void PISAMemoryModel<T>::writeMemory(std::string location, pisa::MultiRegister<T> value)
{
    //const std::lock_guard<std::mutex> lock(parallel_guard);
    if (m_registers.count(location) == 0)
    {
        m_registers[location] = new pisa::MultiRegister<T>();
    }
    *(m_registers[location]) = value;
}

template <typename T>
pisa::MultiRegister<T> &PISAMemoryModel<T>::reference(std::string location)
{
    //const std::lock_guard<std::mutex> lock(parallel_guard);
    return *(m_registers[location]);
}

template <typename T>
pisa::MultiRegister<T> &PISAMemoryModel<T>::operator[](std::string location)
{
    if (m_registers.count(location) == 0)
    {
        m_registers[location] = new pisa::MultiRegister<T>();
    }
    auto &value = *m_registers[location];
    if (value.size() != m_register_width)
        value.resize(m_register_width);

    return value;
}

template <typename T>
pisa::MultiRegister<T> PISAMemoryModel<T>::copy(std::string location)
{
    if (m_registers.count(location) == 0)
    {
        throw std::runtime_error("COPY ERROR: Requested unallocated memory address: " + location);
    }
    return pisa::MultiRegister<T>(*m_registers[location]);
}

template <typename T>
int PISAMemoryModel<T>::registerWidth() const
{
    return m_register_width;
}

template <typename T>
inline void PISAMemoryModel<T>::setRegisterWidth(int newRegister_width)
{
    m_register_width = newRegister_width;
}

template <typename T>
inline const std::unordered_map<std::string, pisa::MultiRegister<T> *> &PISAMemoryModel<T>::registers() const
{
    return m_registers;
}

} // namespace pisa
