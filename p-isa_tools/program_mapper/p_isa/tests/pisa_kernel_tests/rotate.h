// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class RotateOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "rotate_operation"; }

    RotateOperation() :
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

        auto rotate_operation = pisa::poly::rotate().create();
        rotate_operation->setOperationName(rotate_operation->Name());
        rotate_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        rotate_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        rotate_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            rotate_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            rotate_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            rotate_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        rotate_operation->addInput("input0");
        rotate_operation->addOutput("output0");
        program_trace.push_back(rotate_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
