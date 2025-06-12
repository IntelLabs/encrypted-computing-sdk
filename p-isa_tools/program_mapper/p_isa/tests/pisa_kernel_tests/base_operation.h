// Copyright (C) 2023 Intel Corporation

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class BaseOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "base_operation"; }

    BaseOperation() :
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

        auto base_operation = pisa::poly::Add().create();
        base_operation->setOperationName(base_operation->baseName());
        base_operation->setCipherDegree(std::stoi(configuration["CipherDegree"]));
        base_operation->setPolyModulusDegree(pow(2, std::stoi(configuration["Poly_mod_log2"])));
        base_operation->setRnsTerms(std::stoi(configuration["RNS"]));
        if (configuration["Scheme"] == "BGV")
            base_operation->setScheme(SCHEME::BGV);
        else if (configuration["Scheme"] == "CKKS")
        {
            base_operation->setScheme(SCHEME::CKKS);
        }
        else if (configuration["Scheme"] == "BGV")
        {
            base_operation->setScheme(SCHEME::BFV);
        }
        else
            throw std::runtime_error("Invalid Scheme");

        base_operation->addInput("input0");
        base_operation->addInput("input1");
        base_operation->addOutput("output0");
        program_trace.push_back(base_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace.size() << std::endl;
    }
};
