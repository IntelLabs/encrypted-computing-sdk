// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class WideAdd : public PisaKernelTest
{
public:
    static std::string operationName() { return "wide_add"; }

    WideAdd() :
        PisaKernelTest()
    {
        configuration["Name"]           = operationName();
        configuration["Number_of_adds"] = "10";
        configuration["CipherDegree"]   = "2";
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

        number_of_adds = std::stoi(configuration["Number_of_adds"]);
        for (int x = 0; x < number_of_adds; x++)
        {
            auto add_operation = pisa::poly::Add().create();
            add_operation->setOperationName("add");
            add_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
            add_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
            add_operation->setRnsTerms(std::stoi(configuration["RNS"]));
            add_operation->setScheme(SCHEME::BGV);
            add_operation->addInput("a" + std::to_string(x));
            add_operation->addInput("b" + std::to_string(x));
            add_operation->addOutput("a" + std::to_string(x));

            program_trace.push_back(add_operation);
        }
        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }

    int number_of_adds = 20;
};
