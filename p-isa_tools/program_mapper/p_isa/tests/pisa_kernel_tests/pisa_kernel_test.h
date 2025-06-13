// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/poly_program/poly_operation_library.h"
#include <map>
#include <stdexcept>

class PisaKernelTest
{

public:
    PisaKernelTest()
    {
        configuration["Name"]          = "Default";
        configuration["RNS"]           = "8";
        configuration["Key_RNS"]       = "9";
        configuration["Poly_mod_log2"] = "14";
        configuration["Scheme"]        = "BGV";
        program_trace                  = pisa::poly::PolyProgram::create();
    }
    virtual void constructTest()
    {
    }

    const std::shared_ptr<pisa::poly::PolyProgram> getProgramTrace()
    {
        try
        {
            if (created == true)
            {
                return program_trace;
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
    std::shared_ptr<pisa::poly::PolyProgram> program_trace;
    bool created = false;
    std::map<std::string, std::string> configuration;
};
