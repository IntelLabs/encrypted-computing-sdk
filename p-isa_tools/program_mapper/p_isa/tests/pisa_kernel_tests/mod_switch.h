// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class ModSwitchOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "mod_switch_operation"; }

    ModSwitchOperation() :
        PisaKernelTest()
    {
        configuration["Name"]         = operationName();
        configuration["CipherDegree"] = "2";
    };

    // PisaKernelTest interface
public:
    void constructTest() override
    {
        std::cout << "Entered Construct Test" << std::endl;
        std::cout << "Configuration:" << std::endl;
        for (auto config : configuration)
        {
            std::cout << config.first << " : " << config.second << std::endl;
        }

        auto mod_switch_operation = pisa::poly::mod_switch().create();
        mod_switch_operation->setOperationName(mod_switch_operation->Name());
        mod_switch_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        mod_switch_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        mod_switch_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            mod_switch_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            mod_switch_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            mod_switch_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        mod_switch_operation->addInput("input0");
        mod_switch_operation->addOutput("output0");
        program_trace.push_back(mod_switch_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
