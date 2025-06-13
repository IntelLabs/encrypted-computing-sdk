// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class SquareOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "square_operation"; }

    SquareOperation() :
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

        auto square_operation = pisa::poly::square().create();
        square_operation->setOperationName(square_operation->Name());
        square_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        square_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        square_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            square_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            square_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            square_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        square_operation->addInput("input0");
        square_operation->addOutput("output0");
        program_trace.push_back(square_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
