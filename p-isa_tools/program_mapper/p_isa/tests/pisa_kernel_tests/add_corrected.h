// Copyright (C) 2023 Intel Corporation

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"

class AddCorrected : public PisaKernelTest
{
public:
    static std::string operationName() { return "AddCorrected_operation"; }

    AddCorrected() :
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

        auto add_corrected_operation = pisa::poly::library::createPolyOperation("add_corrected");
        program_trace->addOperation(add_corrected_operation);
        program_trace->setScheme(fromString(configuration["Scheme"]));

        add_corrected_operation->setOperationName(add_corrected_operation->Name());

        add_corrected_operation->addInput("input0", std::stoi(configuration["RNS"]), std::stoi(configuration["CipherDegree"]));
        add_corrected_operation->addInput("input1", std::stoi(configuration["RNS"]), std::stoi(configuration["CipherDegree"]));
        add_corrected_operation->addOutput("output0", std::stoi(configuration["RNS"]), std::stoi(configuration["CipherDegree"]));

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace->operations().size() << std::endl;
    }
};
