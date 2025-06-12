// Copyright (C) 2023 Intel Corporation

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class MulPlainOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "mul_plain_operation"; }

    MulPlainOperation() :
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

        auto mul_plain_operation = pisa::poly::mul_plain().create();
        mul_plain_operation->setOperationName(mul_plain_operation->Name());
        mul_plain_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        mul_plain_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        mul_plain_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            mul_plain_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            mul_plain_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            mul_plain_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        mul_plain_operation->addInput("input0");
        mul_plain_operation->addInput("input1");
        mul_plain_operation->addOutput("output0");
        program_trace.push_back(mul_plain_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
