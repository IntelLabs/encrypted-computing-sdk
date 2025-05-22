// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <iostream>
#include <unordered_set>

#include <argmap.h>
#include <config.h>
#if ENABLE_DATA_FORMATS
#include <functional_modeler/data_handlers/hec_dataformats_handler.h>
#endif

#include <functional_modeler/data_handlers/json_data_handler.h>
#include <functional_modeler/pisa_runtime/pisaprogramruntime.h>

#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <common/p_isa/p_isa_performance_modeler.h>
#include <common/p_isa/parser/p_isa_parser.h>
#include <common/timer/timer.h>

using DATA_TYPE = uint32_t;
namespace fs    = std::filesystem;

struct FunctionalModelerArguments
{
    fs::path p_isa_location;
    fs::path json_data_location;
    fs::path graph_image_file_name;
    fs::path raw_input_memory_file;
    fs::path raw_output_memory_file;
    fs::path program_inputs_file;
    fs::path program_outputs_file;
    std::string hardware_model_name           = "example";
    bool verbose                              = false;
    bool render_graph_to_image                = false;
    bool verbose_output_checking              = false;
    bool enable_advanced_debug_tracing        = false;
    bool enable_advanced_performance_analysis = false;
    bool export_inputs_file                   = false;
    bool validate_execution_results           = true;
    bool generate_graphs                      = true;
    bool execute_p_isa_program                = true;
#if ENABLE_DATA_FORMATS
    bool hec_dataformats_mode = false;
#endif
    bool validate_intermediate_results = false;

    // Derived variables
    bool json_data_enabled = false;

#if ENABLE_DATA_FORMATS
    // hec_dataformats
    fs::path hec_dataformats_data_location;
    fs::path hec_dataformats_polynomial_program_location;
#endif

    // Derived
    bool hec_dataformats_data_enabled = false;
};

inline FunctionalModelerArguments parseCommandLineArguments(int argc, char **argv)
{
    FunctionalModelerArguments args;

    //available hardware models
    std::string hardware_model_string = "Available hardware models - (";
    for (auto model : pisa::PerformanceModels::hardwareModels)
    {
        hardware_model_string += model.first + ",";
    }
    hardware_model_string.pop_back();
    hardware_model_string += ")";

    // clang-format off
    argmap::ArgMap()
      .separator(argmap::ArgMap::Separator::WHITESPACE)
      .positional()
      .required()
      .arg("p_isa_op", args.p_isa_location,
           "Location of a file containing a list in CSV format of p_isa instructions", "")
      .named()
      .optional()
      .arg({"--json_data", "--json", "-jd"}, args.json_data_location,
           "Location of a json data file containing HEC formatted data", "")
      .arg({"--input_memory_file", "--imem", "-im"}, args.raw_input_memory_file,
           "Location of a memory file to be read and set as input before executing any instructions", "")
      .arg({"--output_memory_file", "--omem", "-om"}, args.raw_output_memory_file,
             "Location to write a memory file containing all device memory after all instructions have been executed", "")
      .arg({"--program_inputs_file", "--pif", "-if"}, args.program_inputs_file,
             "Location to a file containing program inputs in csv format. Loaded after any memory file(s) and data file but before execution", "")
      .arg({"--program_outputs_file", "--pof", "-of"}, args.program_outputs_file,
             "Location to write a file containing program outputs in csv format. Written after program execution", "")
      .arg({"--graph_file_name", "--gn", "-gf"}, args.graph_image_file_name,
           "Sets the name of the file for the output graph image", "<p_isa_op_file_prefix>.png")
      .arg({"--hardware_model", "-hwm"}, args.hardware_model_name,
         hardware_model_string, "")
#if ENABLE_DATA_FORMATS
      .arg({"--hec_dataformats_data", "--hdd", "-hd"}, args.hec_dataformats_data_location,
            "Location of HEC data-formats data manifest file", "")
      .arg({"--hec_dataformats_poly_program_location", "--hdp", "-pp"}, args.hec_dataformats_polynomial_program_location,
            "Location of HEC data-formats poly program file", "")
#endif
      .toggle()
      .arg({"--verbose", "-v"}, args.verbose,
           "Enables more verbose execution reporting to stdout", "")
      .arg({"--render_graph", "-rg"}, args.render_graph_to_image,
           "Enables rendering of p_isa graph in PNG and DOT file formats", "")
      .arg({"--export_inputs", "-ei"}, args.export_inputs_file,
           "Exports program inputs file to the file specified by --program_inputs_file or program_inputs.csv if none specified", "")
      .arg({"--advanced_performance_analysis", "-apa"}, args.enable_advanced_performance_analysis,
           "Enables advanced performance analysis and cycle count prediction", "")
      .arg({"--verbose_output_checking", "-voc"}, args.verbose_output_checking,
          "Enables functional validation of functional execution", "")
      .arg({"--validate_intermediate_results", "-vir"}, args.validate_intermediate_results,
           "Enables functional validation of intermediates - if --disable_function_validation, this will be automatically set to false", "")
      .arg({"--enable_advanced_debug_tracing", "-dt"}, args.enable_advanced_debug_tracing,
           "Enables advanced debug execution and tracing. Warning: May significantly increase memory usage and reduce performance", "")

#if ENABLE_DATA_FORMATS
      .arg({"--hec_dataformats_mode", "--hdfm", "-hm"}, args.hec_dataformats_mode,
          "Uses hec data-formats execution pipeline", "")
#endif
      .toggle(false)
      .arg({"--disable_graphs", "--graphs", "-g"}, args.generate_graphs,
           "Disables graph building and features", "")
      .arg({"--disable_functional_execution", "--nofunctional"}, args.execute_p_isa_program,
          "Disable functional execution of instruction stream", "")
      .arg({"--disable_functional_validation", "--novalidate", "-nfv"}, args.validate_execution_results,
          "Disables functional validation of functional execution", "")
      .parse(argc, argv);
    // clang-format on

    // Post processing
    if (args.graph_image_file_name.empty())
    {
        args.graph_image_file_name = args.p_isa_location.stem();
        args.graph_image_file_name.replace_extension("png");
    }

    if (args.graph_image_file_name.extension() != ".png")
    {
        std::ostringstream msg;
        msg << "Graph file name must have the extension .png, given "
            << args.graph_image_file_name.extension();
        throw std::runtime_error(msg.str());
    }

    if (args.json_data_location.empty()
#if ENABLE_DATA_FORMATS
        && args.hec_dataformats_data_location.empty()
#endif
    )
    {
        args.validate_execution_results = false;
    }
    else
    {
        if (!args.json_data_location.empty())
        {
            args.json_data_enabled = true;
        }
#if ENABLE_DATA_FORMATS
        else if (args.hec_dataformats_mode && !args.hec_dataformats_polynomial_program_location.empty() && !args.hec_dataformats_data_location.empty())
        {
            args.hec_dataformats_data_enabled = true;
        }
#endif
    }

    return args;
}

template <typename T>
void executePISAInstructions(const FunctionalModelerArguments &arguments, const std::vector<pisa::PISAInstruction *> &instructions, const JSONDataHandler<T> &json_data = {})
{

    try
    {
        if (instructions.size() == 0)
        {
            throw std::runtime_error("No instructions provided");
        }
        pisa::common::SimpleTimer timer;
        PISAProgramRuntime<DATA_TYPE> evaluator;
        evaluator.setDebugMode(arguments.enable_advanced_debug_tracing);

        std::vector<T> modulus_chain;

        if (arguments.json_data_enabled)
        {
            modulus_chain             = json_data.getModulusChain();
            auto ntt_twiddle_factors  = json_data.getNTTTwiddleFactors();
            auto intt_twiddle_factors = json_data.getINTTTwiddleFactors();

            auto inputs     = json_data.getAllInputs();
            auto immediates = json_data.getAllimmediatesAsVec(1);

            evaluator.setModulusChain(modulus_chain);
            auto chain = evaluator.getModulusChain();

            evaluator.setNTTTwiddleFactors(ntt_twiddle_factors);
            evaluator.setINTTTwiddleFactors(intt_twiddle_factors);

            evaluator.setParamMemoryToMultiRegisterDeviceMemory(inputs);
            evaluator.setImmediatesToMultiRegisterDeviceMemory(immediates);
        }
        else
        {
            // Execute evaluator without a data file, generating required values randomly to support execution
            int max_rns        = 0;
            int ntt_poly_mod   = 0;
            int intt_poly_mod  = 0;
            int num_of_factors = pow(2, ntt_poly_mod);
            std::unordered_set<int> galois_elements;

            for (const auto &instruction : instructions)
            {
                max_rns = std::max(instruction->residual(), max_rns);
                if (instruction->Name() == "ntt")
                {
                    ntt_poly_mod = std::max(ntt_poly_mod, instruction->PMD());
                }
                // TODO: Add this for ntt as well - This will always be 1 for now
                else if (instruction->Name() == "intt")
                {
                    galois_elements.insert(instruction->galois_element());
                }
            }

            modulus_chain.reserve(max_rns + 1);
            for (int x = 1; x <= max_rns + 1; x++)
                modulus_chain.push_back(x);

            evaluator.setModulusChain(modulus_chain);

            if (ntt_poly_mod != 0)
            {
                std::vector<std::vector<T>> ntt_twiddle_factors(max_rns + 1, std::vector<T>(num_of_factors));
                TwiddleMap<T> intt_twiddle_factors;
                // TODO: later update when JSON flow supports multiple INTT twiddle factors
                for (int const &ge : galois_elements)
                {
                    intt_twiddle_factors[std::to_string(ge)] = ntt_twiddle_factors;
                }
                evaluator.setNTTTwiddleFactors(ntt_twiddle_factors);
                evaluator.setINTTTwiddleFactors(intt_twiddle_factors);
            }
        }

        if (!arguments.raw_input_memory_file.empty())
            evaluator.setDeviceMemory(*(std::make_shared<std::ifstream>(arguments.raw_input_memory_file).get()));

        /***************/
        auto p_isa_graph = graph::Graph<pisa::PISAInstruction>::createGraph(instructions);

        auto inputs = p_isa_graph.getInputNodes();
        std::vector<std::string> input_register_labels;

        //Retrieve inputs
        for (auto label : inputs)
        {
            input_register_labels.push_back(label.GetDat().label);
        }

        if (arguments.export_inputs_file)
        {
            std::string inputs_file_name = "program_inputs.csv";
            if (!arguments.program_inputs_file.empty())
            {
                inputs_file_name = arguments.program_inputs_file.string();
            }

            std::ofstream input_csv(inputs_file_name);
            evaluator.dumpDeviceMemory(input_csv, input_register_labels);
            input_csv.close();
        }

        //Set inputs
        if (!arguments.program_inputs_file.empty() && arguments.export_inputs_file == false)
        {
            std::ifstream input_read_csv(arguments.program_inputs_file.string());
            evaluator.setDeviceMemory(input_read_csv);
        }
        /*********************/

        bool graph_based_execution = false;
        if (graph_based_execution)
        {
            auto graph             = graph::Graph<pisa::PISAInstruction>::createGraph(instructions);
            auto instruction_graph = graph.getInstructionGraph();
            auto input_layers      = instruction_graph.getGraphInputLayers();
            timer.start();
            evaluator.executeProgram(input_layers);
            timer.stop();
        }
        else
        {
            timer.start();
            evaluator.executeProgram(instructions);
            timer.stop();
        }
        if (!arguments.raw_output_memory_file.empty())
            evaluator.dumpDeviceMemory(*(std::make_shared<std::ofstream>(arguments.raw_output_memory_file).get()));

        std::cout << "Execution: " << timer.elapsedMilliseconds() << "ms" << std::endl;

        /*******************/
        if (!arguments.program_outputs_file.empty())
        {
            auto outputs = p_isa_graph.getOutputNodes();
            std::vector<std::string> output_register_labels;

            for (auto label : outputs)
            {
                output_register_labels.push_back(label.GetDat().label);
            }

            std::ofstream output_csv(arguments.program_outputs_file);
            evaluator.dumpDeviceMemory(output_csv, output_register_labels);
            output_csv.close();
        }

        /*********************/

        if (!arguments.validate_execution_results)
        {
            std::cout << "Validation: NONE" << std::endl;
        }
        else
        {

            bool success = true;
            auto outputs = json_data.getAllOutputs();

            for (const auto &output : outputs)
            {
                auto result = evaluator.getParamMemoryFromMultiRegisterDeviceMemory(output.first);
                std::cout << "Result Comparison for: " << output.first << " = ";
                if (output.second.size() != result.second.size())
                {
                    std::cout << "Warning:: Size of output: " << result.first << " Does not match ground truth\n";
                    success = false;
                    continue;
                }

                for (int x = 0; x < output.second.size(); x++)
                {
                    if (!arguments.verbose_output_checking)
                    {
                        if (output.second[x] != result.second[x])
                            success = false;
                        continue;
                    }

                    if (output.second[x] == result.second[x])
                    {
                        std::cout << x << ": " << output.second[x] << " : " << result.second[x]
                                  << "  : SUCCESS" << std::endl;
                    }
                    else
                    {
                        std::cout << x << ": " << output.second[x] << " : " << result.second[x]
                                  << "  : FAILURE" << std::endl;
                        success = false;
                    }
                }
                std::cout << ((success) ? "SUCCESS" : "FAILURE") << std::endl;
            }

            auto intermediates = json_data.getAllIntermediatess();
            std::cout << "Intermediates: " << intermediates.size() << std::endl;
            for (const auto &intermediate : intermediates)
            {
                auto result = evaluator.getParamMemoryFromMultiRegisterDeviceMemory(intermediate.first);
                std::cout << "Result Comparison for: " << intermediate.first << " = ";
                if (intermediate.second.size() != result.second.size())
                {
                    std::cout << "Warning:: Size of intermediate: " << result.first << " Does not match ground truth\n";
                    success = false;
                    continue;
                }

                for (int x = 0; x < intermediate.second.size(); x++)
                {
                    if (!arguments.verbose_output_checking)
                    {
                        if (intermediate.second[x] != result.second[x])
                            success = false;
                        continue;
                    }

                    if (intermediate.second[x] == result.second[x])
                    {
                        std::cout << x << ": " << intermediate.second[x] << " : " << result.second[x]
                                  << "  : SUCCESS" << std::endl;
                    }
                    else
                    {
                        std::cout << intermediate.second[x] << " : " << result.second[x]
                                  << "  : FAILURE" << std::endl;
                        success = false;
                    }
                }
                std::cout << ((success) ? "SUCCESS" : "FAILURE") << std::endl;
            }

            std::cout << "Validation: " << ((success) ? "SUCCESS" : "FAILURE") << std::endl;
        }

        if (arguments.enable_advanced_performance_analysis)
        {
            pisa::performance::PISAPerformanceModeler m_performance_model;
            m_performance_model.setInstructionStream(instructions);
            m_performance_model.generateAndPrintPerformanceReport(pisa::PerformanceModels::hardwareModels[arguments.hardware_model_name]);
        }
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during" << __FUNCTION__ << ", err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << " in file " << __FILE__ << std::endl;
        throw;
    }
}

#if ENABLE_DATA_FORMATS
template <typename T>
void executePISAInstructions_Dataformats(const FunctionalModelerArguments &arguments, const std::vector<pisa::PISAInstruction *> &instructions, const HecDataFormatsHandler<T> &dataformats_data = {})
{

    try
    {
        if (instructions.size() == 0)
        {
            throw std::runtime_error("No instructions provided");
        }
        pisa::common::SimpleTimer timer;
        PISAProgramRuntime<DATA_TYPE> evaluator;

        std::vector<T> modulus_chain;

        if (arguments.hec_dataformats_data_enabled)
        {
            modulus_chain             = dataformats_data.getModulusChain();
            auto ntt_twiddle_factors  = dataformats_data.getNTTTwiddleFactors();
            auto intt_twiddle_factors = dataformats_data.getINTTTwiddleFactors();

            auto inputs     = dataformats_data.getAllInputs();
            auto immediates = dataformats_data.getAllimmediatesAsVec(1);
            evaluator.setModulusChain(modulus_chain);
            auto chain = evaluator.getModulusChain();

            evaluator.setNTTTwiddleFactors(ntt_twiddle_factors);
            evaluator.setINTTTwiddleFactors(intt_twiddle_factors);

            evaluator.setParamMemoryToMultiRegisterDeviceMemory(inputs);
            evaluator.setImmediatesToMultiRegisterDeviceMemory(immediates);
        }
        else
        {
            // Execute evaluator without a data file, generating required values randomly to support execution
            int max_rns        = 0;
            int ntt_poly_mod   = 0;
            int intt_poly_mod  = 0;
            int num_of_factors = pow(2, ntt_poly_mod);

            std::unordered_set<int> galois_elements;
            for (const auto &instruction : instructions)
            {
                max_rns = std::max(instruction->residual(), max_rns);
                if (instruction->Name() == "ntt")
                {
                    ntt_poly_mod = std::max(ntt_poly_mod, instruction->PMD());
                }
                else if (instruction->Name() == "intt")
                    galois_elements.insert(instruction->galois_element());
            }

            modulus_chain.reserve(max_rns + 1);
            for (int x = 1; x <= max_rns + 1; x++)
                modulus_chain.push_back(x);

            evaluator.setModulusChain(modulus_chain);

            if (ntt_poly_mod != 0)
            {
                std::vector<std::vector<T>> ntt_twiddle_factors(max_rns + 1, std::vector<T>(num_of_factors));
                evaluator.setNTTTwiddleFactors(ntt_twiddle_factors);
                TwiddleMap<T> intt_twiddle_factors;
                for (int const &ge : galois_elements)
                {
                    intt_twiddle_factors[std::to_string(ge)] = ntt_twiddle_factors;
                }
                evaluator.setINTTTwiddleFactors(intt_twiddle_factors);
            }
        }

        bool graph_based_execution = false;
        if (graph_based_execution)
        {
            auto graph             = graph::Graph<pisa::PISAInstruction>::createGraph(instructions);
            auto instruction_graph = graph.getInstructionGraph();
            auto input_layers      = instruction_graph.getGraphInputLayers();
            timer.start();
            evaluator.executeProgram(input_layers);
            timer.stop();
        }
        else
        {
            timer.start();
            evaluator.executeProgram(instructions);
            timer.stop();
        }
        //evaluator.getMemory(output_locations);
        std::cout << "Execution: " << timer.elapsedMilliseconds() << "ms" << std::endl;

        if (!arguments.validate_execution_results)
        {
            std::cout << "Validation: NONE" << std::endl;
            return;
        }

        bool success = true;
        auto outputs = dataformats_data.getAllOutputs();

        for (const auto &output : outputs)
        {
            auto result = evaluator.getParamMemoryFromMultiRegisterDeviceMemory(output.first);
            std::cout << "Result Comparison for: " << output.first << " = ";
            if (output.second.size() != result.second.size())
                throw std::runtime_error("Size of output: " + result.first + " Does not match ground truth");
            for (int x = 0; x < output.second.size(); x++)
            {
                if (!arguments.verbose_output_checking)
                {
                    if (output.second[x] != result.second[x])
                        success = false;
                    continue;
                }

                if (output.second[x] == result.second[x])
                {
                    std::cout << x << ": " << output.second[x] << " : " << result.second[x]
                              << "  : SUCCESS" << std::endl;
                }
                else
                {
                    std::cout << x << ": " << output.second[x] << " : " << result.second[x]
                              << "  : FAILURE" << std::endl;
                    success = false;
                }
            }
            std::cout << ((success) ? "SUCCESS" : "FAILURE") << std::endl;
        }

        std::vector<std::pair<std::string, std::vector<T>>> intermediates;
        if (arguments.validate_intermediate_results)
            intermediates = dataformats_data.getAllIntermediates();

        std::cout << "Intermediates: " << intermediates.size() << std::endl;
        for (const auto &intermediate : intermediates)
        {
            auto result = evaluator.getParamMemoryFromMultiRegisterDeviceMemory(intermediate.first);
            std::cout << "Result Comparison for: " << intermediate.first << " = ";
            if (intermediate.second.size() != result.second.size())
                throw std::runtime_error("Size of output: " + result.first + " Does not match ground truth");

            for (int x = 0; x < intermediate.second.size(); x++)
            {
                if (!arguments.verbose_output_checking)
                {
                    if (intermediate.second[x] != result.second[x])
                        success = false;
                    continue;
                }

                if (intermediate.second[x] == result.second[x])
                {
                    std::cout << x << ": " << intermediate.second[x] << " : " << result.second[x]
                              << "  : SUCCESS" << std::endl;
                }
                else
                {
                    std::cout << intermediate.second[x] << " : " << result.second[x]
                              << "  : FAILURE" << std::endl;
                    success = false;
                }
            }
            std::cout << ((success) ? "SUCCESS" : "FAILURE") << std::endl;
        }

        std::cout << "Validation: " << ((success) ? "SUCCESS" : "FAILURE") << std::endl;

        if (arguments.enable_advanced_performance_analysis)
        {
            pisa::performance::PISAPerformanceModeler m_performance_model;
            m_performance_model.setInstructionStream(instructions);
            m_performance_model.generateAndPrintPerformanceReport();
        }
    }
    catch (...)
    {
        throw;
    }
}
#endif

int main(int argc, char **argv)
{
    try
    {
        const auto arguments = parseCommandLineArguments(argc, argv);

        std::vector<pisa::PISAInstruction *> p_isa_instructions = pisa::PISAParser::parse(arguments.p_isa_location);

        if (arguments.generate_graphs)
        {
            auto p_isa_graph = graph::Graph<pisa::PISAInstruction>::createGraph(p_isa_instructions);
            printGraphInformation(p_isa_graph, "***P_ISA Operation graph information***");

            if (arguments.render_graph_to_image)
            {
                std::cout << "Rendering graph image to: " << arguments.graph_image_file_name << std::endl;
                p_isa_graph.renderGraphToPNGDot(arguments.graph_image_file_name, graph::NAME);
            }
        }

        if (arguments.verbose)
            std::cout << "Instruction count: " << p_isa_instructions.size() << std::endl;

        if (arguments.json_data_enabled)
        {
            JSONDataHandler<DATA_TYPE> input_parser;
            input_parser = JSONDataHandler<DATA_TYPE>(arguments.json_data_location, true);
            if (arguments.execute_p_isa_program)
            {
                executePISAInstructions(arguments, p_isa_instructions, input_parser);
            }
        }
#if ENABLE_DATA_FORMATS
        else if (arguments.hec_dataformats_data_enabled)
        {
            HecDataFormatsHandler<DATA_TYPE> hec_dataformats_input_parser;
            hec_dataformats_input_parser = HecDataFormatsHandler<DATA_TYPE>(arguments.hec_dataformats_polynomial_program_location, arguments.hec_dataformats_data_location);
            if (arguments.execute_p_isa_program)
            {
                executePISAInstructions_Dataformats(arguments, p_isa_instructions, hec_dataformats_input_parser);
            }
        }
#endif
        else
        {
            executePISAInstructions(arguments, p_isa_instructions, JSONDataHandler<uint>());
        }

        return EXIT_SUCCESS;
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Caught std::runtime_error in main: " << err.what() << std::endl;
        std::cout << "Validation: CRASHED\n"
                  << std::endl;

        std::cerr << "ERROR: " << err.what() << '\n'
                  << std::endl;
        return EXIT_FAILURE;
    }
    catch (...)
    {
        std::cout << "Validation: CRASHED " << std::endl;

        std::cerr << "ERROR: UNKNOWN error " << std::endl;
        return EXIT_FAILURE;
    }
}
