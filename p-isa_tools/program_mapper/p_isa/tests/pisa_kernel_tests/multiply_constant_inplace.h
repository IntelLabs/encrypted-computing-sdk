// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class MultiplyConstantInplaceOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "multiply_constant_inplace_operation"; }

    MultiplyConstantInplaceOperation() :
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

        auto multiply_constant_inplace_operation = pisa::poly::multiply_constant_inplace().create();
        multiply_constant_inplace_operation->setOperationName(multiply_constant_inplace_operation->Name());
        multiply_constant_inplace_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        multiply_constant_inplace_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        multiply_constant_inplace_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            multiply_constant_inplace_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            multiply_constant_inplace_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            multiply_constant_inplace_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        multiply_constant_inplace_operation->addInput("inputoutput0");
        multiply_constant_inplace_operation->addOutput("inputoutput0");
        program_trace.push_back(multiply_constant_inplace_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
