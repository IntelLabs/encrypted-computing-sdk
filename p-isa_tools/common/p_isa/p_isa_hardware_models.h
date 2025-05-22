// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <common/p_isa/p_isa_instructions.h>
#include <map>
#include <string>

namespace pisa::PerformanceModels {

struct InstructionPerfCharacteristics
{
    InstructionPerfCharacteristics() = default;
    InstructionPerfCharacteristics(int _throughput, int _latency) :
        throughput(_throughput),
        latency(_latency)
    {
    }

    int throughput = 1;
    int latency    = 1;
};

class PISAHardwareModel
{
public:
    std::map<std::string, InstructionPerfCharacteristics> ISAInstructionPerformanceMap;
    // Memory behavior performance map
    std::map<std::string, InstructionPerfCharacteristics> ISAInstructionMemoryMap;
    std::map<std::string, uint64_t> MemorySizesMap;
};

class ExampleHardware : public PISAHardwareModel
{
public:
    ExampleHardware()
    {
        ISAInstructionPerformanceMap = {
            { pisa::instruction::Add::baseName, InstructionPerfCharacteristics(8192, 8192) },
            { pisa::instruction::Sub::baseName, InstructionPerfCharacteristics(8192, 8192) },
            { pisa::instruction::Mul::baseName, InstructionPerfCharacteristics(8192, 8192) },
            { pisa::instruction::Mac::baseName, InstructionPerfCharacteristics(8192, 8192) },
            { pisa::instruction::Maci::baseName, InstructionPerfCharacteristics(8192, 8192) },
            { pisa::instruction::Intt::baseName, InstructionPerfCharacteristics(8192 * 6, 8192 * 6) },
            { pisa::instruction::Ntt::baseName, InstructionPerfCharacteristics(8192 * 6, 8192 * 6) },
            { pisa::instruction::Muli::baseName, InstructionPerfCharacteristics(8192, 8192) }
        };

        // Memory behavior performance map
        ISAInstructionMemoryMap = {
            { "MEMORY", InstructionPerfCharacteristics(1, 40) },
            { "MEMORY_CACHE", InstructionPerfCharacteristics(5, 44) },
            { "CACHE", InstructionPerfCharacteristics(4, 4) },
            { "REGISTER", InstructionPerfCharacteristics(1, 1) },

        };

        MemorySizesMap = {
            { "MEMORY", uint64_t(1572000) },
            { "CACHE", uint64_t(1572000) },
            { "REGISTER", uint64_t(1572000) },

        };
    }
};

class Model1 : public PISAHardwareModel
{
public:
    Model1()
    {
        ISAInstructionPerformanceMap = {
            { pisa::instruction::Add::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Sub::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Mul::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Mac::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Maci::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Intt::baseName, InstructionPerfCharacteristics(1, 33) },
            { pisa::instruction::Ntt::baseName, InstructionPerfCharacteristics(1, 33) },
            { pisa::instruction::Muli::baseName, InstructionPerfCharacteristics(1, 6) }
        };

        // Memory behavior performance map
        ISAInstructionMemoryMap = {
            { "MEMORY", InstructionPerfCharacteristics(1, 40) },
            { "MEMORY_CACHE", InstructionPerfCharacteristics(5, 44) },
            { "CACHE", InstructionPerfCharacteristics(4, 4) },
            { "REGISTER", InstructionPerfCharacteristics(1, 1) },

        };

        MemorySizesMap = {
            { "MEMORY", uint64_t(1572000) },
            { "CACHE", uint64_t(1572000) },
            { "REGISTER", uint64_t(1572000) },

        };
    }
};

class Model2 : public PISAHardwareModel
{
public:
    Model2()
    {
        ISAInstructionPerformanceMap = {
            { pisa::instruction::Add::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Sub::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Mul::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Mac::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Maci::baseName, InstructionPerfCharacteristics(1, 6) },
            { pisa::instruction::Intt::baseName, InstructionPerfCharacteristics(1, 33) },
            { pisa::instruction::Ntt::baseName, InstructionPerfCharacteristics(1, 33) },
            { pisa::instruction::Muli::baseName, InstructionPerfCharacteristics(1, 6) }
        };

        // Memory behavior performance map
        ISAInstructionMemoryMap = {
            { "MEMORY", InstructionPerfCharacteristics(1, 40) },
            { "MEMORY_CACHE", InstructionPerfCharacteristics(5, 44) },
            { "CACHE", InstructionPerfCharacteristics(4, 4) },
            { "REGISTER", InstructionPerfCharacteristics(1, 1) },

        };

        MemorySizesMap = {
            { "MEMORY", uint64_t(1572000) },
            { "CACHE", uint64_t(2048) },
            { "REGISTER", uint64_t(256) },

        };
    }
};

static std::map<std::string, PISAHardwareModel> hardwareModels = { { "example", ExampleHardware() }, { "model1", Model1() }, { "model2", Model2() } };

} // namespace pisa::PerformanceModels
