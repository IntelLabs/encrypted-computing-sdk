// Copyright (C) 2023 Intel Corporation

#pragma once

#include "program_mapper/p_isa/pisa_test_generator.h"
#include "program_mapper/p_isa/tests/pisa_kernel_tests/pisa_kernel_test.h"
#include <cmath>

class AddOperation : public PisaKernelTest
{
public:
    static std::string operationName() { return "add_operation"; }

    AddOperation() :
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

        //FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, RNS_TERM, CIPHER_DEGREE, OP_NAME, OUTPUT_ARGUMENT, INPUT_ARGUMENT, INPUT_ARGUMENT

        auto add_operation = pisa::poly::library::createPolyOperation("add",
                                                                      { configuration["Scheme"],
                                                                        configuration["Poly_mod_log2"],
                                                                        configuration["Key_RNS"],
                                                                        configuration["RNS"],
                                                                        configuration["CipherDegree"],
                                                                        "add",
                                                                        "output0",
                                                                        "input0",
                                                                        "input1" },
                                                                      program_trace);

        program_trace->addOperation(add_operation);

        created = true;
        std::cout << "Created program trace, program trace size: " << program_trace->operations().size() << std::endl;
    }
};
