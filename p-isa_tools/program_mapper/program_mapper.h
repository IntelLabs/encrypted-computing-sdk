// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>

#include "p_isa/pisa_test_generator.h"
#include "utility_functions.h"
#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <common/timer/timer.h>
#include <functional_modeler/data_handlers/json_data_handler.h>
#include <program_mapper/p_isa/pisa_graph_optimizer.h>
#include <program_mapper/p_isa/pisakernel.h>
#include <program_mapper/trace_parser/program_trace_helper.h>

namespace pisa {

using DATA_TYPE = uint32_t;
namespace fs    = std::filesystem;

struct ProgramMapperArguments
{
    fs::path program_trace_location;
    fs::path outfile_prefix;
    fs::path kerngen;
    fs::path dot_file_name;
    fs::path cache_dir         = "./kernel_cache";
    fs::path out_dir           = "./";
    fs::path generated_name    = "";
    bool verbose               = false;
    bool export_dot            = false;
    bool output_memory_bank    = false;
    bool remove_cache          = false;
    bool new_kerngen           = true;
    bool generate_graphs       = true;
    bool apply_name_spacing    = true;
    bool use_kernel_cache      = true;
    std::string kernel_library = "HDF";
    bool export_program_trace  = false;
    bool enable_intermediates  = false;
};

template <typename T>
class ProgramMapper
{
public:
    ProgramMapper()
    {
    }

    void generatePisaProgramFromHEProgram(std::shared_ptr<pisa::poly::PolyProgram> program_trace);

    // Generate PISAKernels(ninja kernels) as needed by the program trace.
    // Checks for each kernel the HE operation and parameters and calls
    // kerngen.py to generate the ninja kernel if it does not already
    // exist in the kernel_cache.
    std::vector<pisa::kernel::PISAKernel *> generatePISAKernelsFromHEOperationVector(std::vector<std::shared_ptr<pisa::poly::PolyOperation>> operations, std::string kerngen_loc, int &max_rns_terms);

    void mapKernelInputOutputToRegisterMap(std::vector<kernel::PISAKernel *> &p_isa_kernels, const std::vector<std::shared_ptr<pisa::poly::PolyOperation>> &program_trace,
                                           std::map<std::string, std::string> &register_map, std::vector<std::pair<std::string, std::vector<T>>> immediates = std::vector<std::pair<std::string, std::vector<T>>>());
    std::map<std::string, std::string> mapProgramTraceOperationsIntoRegisterMap(std::vector<std::shared_ptr<pisa::poly::PolyOperation>> program_trace, std::map<std::string, std::string> register_map = std::map<std::string, std::string>());
    std::vector<pisa::PISAInstruction *> outputCombinedPisaInstructions(std::vector<kernel::PISAKernel *> p_isa_kernels, bool apply_namespacing);

    const ProgramMapperArguments &getArguments() const;
    void setArguments(const ProgramMapperArguments &newArguments);

    ProgramMapperArguments arguments;
};

} // namespace pisa
#include "program_mapper.cpp"
