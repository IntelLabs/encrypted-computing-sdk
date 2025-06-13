// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>

#include "p_isa/pisa_test_generator.h"
#include "program_mapper.h"
#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <common/timer/timer.h>
#include <functional_modeler/data_handlers/json_data_handler.h>
#include <program_mapper/p_isa/pisa_graph_optimizer.h>
#include <program_mapper/p_isa/pisakernel.h>
#include <program_mapper/trace_parser/program_trace_helper.h>

#include <argmap.h>

using DATA_TYPE = uint32_t;
namespace fs    = std::filesystem;

inline pisa::ProgramMapperArguments parseCommandLineArguments(int argc, char **argv)
{
    pisa::ProgramMapperArguments args;
    // clang-format off
    argmap::ArgMap()
        .separator(argmap::ArgMap::Separator::WHITESPACE)
        .required()
        .positional()
        .arg("program_trace", args.program_trace_location,
          "Location of a file containing a list in csv format for p_isa instructions", "")
        .arg("kerngen_loc", args.kerngen, "Location of the kerngen.py file", "")
        .optional()
        .toggle()
        .arg({"--verbose", "-v"}, args.verbose,"Enables more verbose execution reporting to std out", "")
        .arg({"--export_dot", "-ed"}, args.export_dot, "Export polynomial program and p_isa program graphs to dot file format", "")
        .arg({"--remove_cache", "--rm_cache", "-rc"}, args.remove_cache,
          "Remove the kernel cache directory at the end of the program", "")
        .arg({"--enable_memory_bank_output", "--banks", "-b"}, args.output_memory_bank,
          "Will output P-ISA programs with registers that include hard coded memory banks when enabled", "")
        .arg({"--export_trace", "-pb"}, args.export_program_trace,"Exports trace to opposite of input format, CSV <-> Pb", "")
        .arg({"--enable_intermediates", "-ei"}, args.enable_intermediates,"Enables intermediates by disabling name spacing and other optimizations on intermediate values", "")
        .toggle(false)
        .arg({"--disable_graphs", "--graphs", "-g"}, args.generate_graphs,
          "Disables graph building and features", "")
        .arg({"--disable_namespace", "--nns", "-n"}, args.apply_name_spacing,
          "Disables applying register name spacing on PISAKernel nodes", "")
        .arg({"--disable_cache", "--no_cache", "-dc"}, args.use_kernel_cache,
          "Disables the use of a cache for Ninja kernels", "")
        .named()
        .arg({"--dot_file_name", "-df"}, args.dot_file_name , "Sets the name of the output dot file", "")
        .arg({"--cache_dir", "--cache", "-c"}, args.cache_dir, "Sets the name of the kernel cache directory")
        .arg({"--out_dir", "--out", "-o"}, args.out_dir, "Sets the location for all output files")
        .arg({"--generated_json", "--generate", "-gen"}, args.generated_name, "Enables generation of JSON data file and specifies name")
        .arg({"--kernel_library", "--kernlib", "-kl"}, args.kernel_library, "Specifies which kernel library to use.")
        .parse(argc, argv);
    // clang-format on

    // Post-processing of positional arguments
    auto strip_substring = [&path = args.program_trace_location](const std::string &substr) -> fs::path {
        auto ret = path.stem();
        auto pos = ret.string().find(substr);
        if (pos != std::string::npos)
        {
            ret = ret.string().erase(pos, substr.size());
        }
        return ret;
    };

    args.outfile_prefix = args.out_dir / (strip_substring("_program_trace").string() + "_pisa");
    if (args.dot_file_name.empty())
    {
        args.dot_file_name = args.out_dir / args.program_trace_location.stem();
        args.dot_file_name.replace_extension("dot");
    }

    return args;
}

int main(int argc, char **argv)
{
    try
    {
        auto arguments = parseCommandLineArguments(argc, argv);

        std::shared_ptr<pisa::poly::PolyProgram> program_trace;
        // Parses a polynomial program into a vector of HEOPerations

        if (arguments.program_trace_location.extension() == ".csv")
        {
            program_trace = PolynomialProgramHelper::parse(arguments.program_trace_location, POLYNOMIAL_PROGRAM_FORMAT::CSV);
#ifdef ENABLE_DATA_FORMATS
            if (arguments.export_program_trace)
            {
                PolynomialProgramHelper::writeTraceToProtoBuff(program_trace, arguments.program_trace_location.filename().string() + ".bin");
            }
#endif
        }
#ifdef ENABLE_DATA_FORMATS
        else if (arguments.program_trace_location.extension() == ".bin")
        {
            program_trace = PolynomialProgramHelper::parse(arguments.program_trace_location, POLYNOMIAL_PROGRAM_FORMAT::PROTOBUFF);
            if (arguments.export_program_trace)
            {
                PolynomialProgramHelper::writeTraceToCSV(program_trace, arguments.program_trace_location.filename().string() + ".csv");
            }
        }
#endif
        else
        {
            throw std::runtime_error("Unsupported data format");
        }

        if (arguments.verbose)
            std::cout << "Instruction count: " << program_trace->operations().size() << std::endl;

        pisa::ProgramMapper<DATA_TYPE> program_mapper;
        program_mapper.setArguments(arguments);
        program_mapper.generatePisaProgramFromHEProgram(program_trace);

        return 0;
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Caught std::runtime_error in main: " << err.what() << std::endl;
        return 1;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in main" << std::endl;
        return 1;
    }
}
