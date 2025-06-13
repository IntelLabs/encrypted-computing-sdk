// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class MulOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "mul_operation"; }

    MulOperation() :
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

        auto mul_operation = pisa::poly::Mul().create();
        mul_operation->setOperationName(mul_operation->Name());
        mul_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        mul_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        mul_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            mul_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            mul_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            mul_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        mul_operation->addInput("input0");
        mul_operation->addInput("input1");
        mul_operation->addOutput("output0");
        program_trace.push_back(mul_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
