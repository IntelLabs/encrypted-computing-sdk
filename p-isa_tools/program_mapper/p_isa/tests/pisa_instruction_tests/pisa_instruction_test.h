// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <common/p_isa/p_isa.h>
#include <common/p_isa/p_isa_instructions.h>
#include <map>
#include <stdexcept>

class PisaInstructionTest
{

public:
    PisaInstructionTest()
    {
        configuration["Name"]          = "Default";
        configuration["RNS_INDEX"]     = "0";
        configuration["Poly_mod_log2"] = "14";
        configuration["Chunk_INDEX"]   = "0";
    }
    virtual void constructTest()
    {
    }

    const std::vector<pisa::PISAInstruction *> &getInstructionTrace()
    {
        try
        {
            if (created == true)
            {
                return instruction_trace;
            }
            else
                throw std::runtime_error("Tried to use without creating first");
        }
        catch (...)
        {
            throw;
        }
    }

    std::map<std::string, std::string> &getConfiguration()
    {
        return configuration;
    }

protected:
    std::vector<pisa::PISAInstruction *> instruction_trace;
    bool created = false;
    std::map<std::string, std::string> configuration;
};
