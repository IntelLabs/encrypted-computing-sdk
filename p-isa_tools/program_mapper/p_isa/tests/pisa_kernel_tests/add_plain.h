// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class AddPlain : public PisaKernelTest
{
public:
    static std::string operationName() { return "add_plain_operation"; }

    AddPlain() :
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

        auto add_plain_operation = pisa::poly::add_plain().create();
        add_plain_operation->setOperationName(add_plain_operation->Name());
        add_plain_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        add_plain_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        add_plain_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            add_plain_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            add_plain_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            add_plain_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        add_plain_operation->addInput("input0");
        add_plain_operation->addInput("input1");
        add_plain_operation->addOutput("output0");
        program_trace.push_back(add_plain_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
