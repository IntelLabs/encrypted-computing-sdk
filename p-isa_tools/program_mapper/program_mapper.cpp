// Copyright (C) 2023 Intel Corporation

#include "program_mapper.h"

namespace pisa {

template <typename T>
void ProgramMapper<T>::generatePisaProgramFromHEProgam(std::shared_ptr<pisa::poly::PolyProgram> program_trace)
{
    // Generates a map from raw seal trace to V0 trace to allow for
    // input/output variable name alignment with trace file to support
    // validation.
    std::map<std::string, std::string> register_map;

    auto program_graph   = graph::Graph<pisa::poly::PolyOperation>::createGraph(program_trace->operationsRaw());
    auto program_inputs  = program_graph.getInputNodes(true, true, false);
    auto program_outputs = program_graph.getOutputNodes();
    for (auto input : program_inputs)
    {
        register_map[input.GetDat().label] = input.GetDat().label;
    }
    for (auto output : program_outputs)
    {
        register_map[output.GetDat().label] = output.GetDat().label;
    }

    if (arguments.enable_intermediates == true)
    {
        auto all_program_data_nodes = program_graph.getDataGraph();
        for (auto data : all_program_data_nodes.getNodes())
        {
            register_map[data.GetDat().label] = data.GetDat().label;
        }
    }

    // Generates map mapping all input and output locations in the program
    // trace not part of the program_trace input/output set to include
    // operation namespace.
    // This is used for efficiently linking HE_Operations together.
    // Currently input/output operations are determined via the trace @TODO
    // better to switch this to graph based approach
    // and simply raise warnings when there is a mismatch between graph and
    // trace. A middle term solution maybe to create option to use a handinput_parser_v0
    // aligned map.
    register_map = mapProgramTraceOperationsIntoRegisterMap(program_trace->operations(), register_map);

    // Generate PISAKernels(ninja kernels) as needed by the program trace.
    // Checks for each kernel the HE operation and parameters and calls
    // kerngen.py to generate the ninja kernel if it does not already
    // exist in the kernel_cache.

    int max_rns_term   = 0;
    auto p_isa_kernels = generatePISAKernelsFromHEOperationVector(program_trace->operations(), arguments.kerngen, max_rns_term);

    /* Remaps kernel input/output names based upon the trace mapping There
     * exists a 1 : 1 mapping between HEOperation -> PISAKernel, this
     * function aligns the PISA input/output names to match HEOperation
    */
    mapKernelInputOutputToRegisterMap(p_isa_kernels, program_trace->operations(), register_map);

    // Generates a vector containing all of the remapped instructions for
    // all of the p_isa_kernels resulting in a single set of all P-ISA
    // instructions necessary to execute
    // the operations specified in the seal trace.
    auto combined_instructions = outputCombinedPisaInstructions(p_isa_kernels, arguments.apply_name_spacing);

    /* Apply instruction graph rewritter and instruction hardware fixes and optimization */
    PISAGraphOptimizer graph_optimizer;
    graph_optimizer.applyDuplicateInputVariableSeperation(combined_instructions);

    /* generates graph from combined p_isa instructions */
    auto p_isa_graph      = graph::Graph<pisa::PISAInstruction>::createGraph(combined_instructions);
    combined_instructions = graph_optimizer.generateInstructionStreamFromGraph(p_isa_graph, true, combined_instructions);

    /* Re-generate combined instructions as needed */
    if (arguments.generated_name != "")
    {
        PisaTestGenerator test_gen;
        auto generated_json = test_gen.generateJSONForGraph(p_isa_graph);
        test_gen.populateCalculatedOutputResults(combined_instructions, generated_json);
        test_gen.writeJSON(generated_json, arguments.generated_name);
    }

    /* renders instructions from graph, Current renders two graphs, the
     * seal program trace graph at the HEOperation level and the P-ISA
     * instruction level graph*/
    if (arguments.generate_graphs)
    {

        if (arguments.export_dot)
        {
            std::cout << "Writing graph to dot file: " << arguments.dot_file_name << std::endl;
            std::string dot_file_name = arguments.outfile_prefix.replace_extension("dot");
#pragma omp parallel sections
            {
#pragma omp section
                program_graph.writeDotFile(arguments.dot_file_name, graph::NAME);
#pragma omp section
                p_isa_graph.writeDotFile(dot_file_name, graph::NAME);
            } // End of parallel region

            auto inputs = p_isa_graph.getInputNodes();
            std::cout << "P_ISA Graph Input Nodes\n"
                      << graph::with_delimiter(inputs, "\n");
        }
    }

    /* Outputs the combined p_isa_kernel to an instruction stream,
     * PISAInstructions are implemented so that they print out functionally
     * with stream operator
    */
    const auto final_kernel_filename = arguments.outfile_prefix.replace_extension("csv");
    writeToFileBy(final_kernel_filename.string(), combined_instructions,
                  [membank = arguments.output_memory_bank](auto *instruction) {
                      instruction->setOutputBlock(membank);
                      return *instruction;
                  });

    if (arguments.verbose)
    {
        for (const auto &instruction : combined_instructions)
            std::cout << *instruction << std::endl;
    }

    /* generates memory file for p_isa_graph */
    std::vector<std::string> mem_file = generateMemFile(p_isa_graph, max_rns_term);
    const auto memory_filename        = arguments.outfile_prefix.replace_extension("tw.mem");
    writeToFileBy(memory_filename.string(), mem_file, [](const auto &line) { return line; });

    return;
}

template <typename T>
std::vector<kernel::PISAKernel *> ProgramMapper<T>::generatePISAKernelsFromHEOperationVector(std::vector<std::shared_ptr<pisa::poly::PolyOperation>> program_trace,
                                                                                             std::string kerngen_loc, int &max_rns_term)
{
    try
    {
        auto kernel_cache = pisa::kernel::Cache(arguments.cache_dir, arguments.use_kernel_cache, arguments.remove_cache);
        std::vector<pisa::kernel::PISAKernel *> p_isa_kernels(program_trace.size());

        std::transform(program_trace.begin(), program_trace.end(), p_isa_kernels.begin(),
                       [&kernel_cache, &max_rns_term, &kerngen_loc, this](auto s) {
                           // max_rns_term = std::max(max_rns_term, s->getRnsTerms());
                           auto kernel = pisa::kernel::PISAKernel::create(kerngen_loc, s.get(), kernel_cache, arguments.verbose, arguments.new_kerngen, arguments.kernel_library);
                           //Graph variable extraction
                           kernel->determineVariableNamingViaGraph();
                           return kernel;
                       });

        return p_isa_kernels;
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during kernel generation, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}

template <typename T>
void ProgramMapper<T>::mapKernelInputOutputToRegisterMap(std::vector<kernel::PISAKernel *> &p_isa_kernels, const std::vector<std::shared_ptr<pisa::poly::PolyOperation>> &program_trace,
                                                         std::map<std::string, std::string> &register_map, std::vector<std::pair<std::string, std::vector<T>>> immediates)
{

    for (int y = 0; y < program_trace.size(); y++)
    {
        std::shared_ptr<pisa::poly::PolyOperation> i = program_trace[y];
        for (int x = 0; x < i->numInputOperands(); x++)
        {
            std::string name = register_map[i->getInputOperand(x).location()];
            p_isa_kernels[y]->mapInput(x, name);
        }
        for (int x = 0; x < i->numOutputOperands(); x++)
        {
            std::string name = register_map[i->getOutputOperand(x).location()];
            p_isa_kernels[y]->mapOutput(x, name);
        }
    }
}

// Generates map mapping all input and output locations in the program
// trace not part of the program_trace input/output set to include
// operation namespace.
// This is used for efficiently linking HE_Operations together.
// Currently input/output operations are determined via the trace @TODO
// better to switch this to graph based approach
// and simply raise warnings when there is a mismatch between graph and
// trace. A middle term solution maybe to create option to use a hand
// aligned map
template <typename T>
std::map<std::string, std::string> ProgramMapper<T>::mapProgramTraceOperationsIntoRegisterMap(std::vector<std::shared_ptr<pisa::poly::PolyOperation>> program_trace,
                                                                                              std::map<std::string, std::string> register_map)
{

    for (int x = 0; x < program_trace.size(); x++)
    {
        std::string location;
        for (int y = 0; y < program_trace[x]->numInputOperands(); y++)
        {
            location          = program_trace[x]->getInputOperand(y).location();
            std::string value = register_map[location];
            if (value.size() == 0)
            {
                register_map[location] = program_trace[x]->Name() + std::to_string(x) + "input" + std::to_string(y);
            }
        }
        for (int y = 0; y < program_trace[x]->numOutputOperands(); y++)
        {
            location          = program_trace[x]->getOutputOperand(y).location();
            std::string value = register_map[location];
            if (value.size() == 0)
            {
                register_map[location] = program_trace[x]->Name() + std::to_string(x) + "output" + std::to_string(y);
            }
        }
    }
    return register_map;
}

template <typename T>
std::vector<PISAInstruction *> ProgramMapper<T>::outputCombinedPisaInstructions(std::vector<kernel::PISAKernel *> p_isa_kernels, bool apply_namespacing)
{
    std::vector<pisa::PISAInstruction *> combined_instructions;
    for (const auto &kernel : p_isa_kernels)
    {
        kernel->setEnableNamespace(apply_namespacing);
        const auto &instructions = kernel->getMappedInstructions();
        combined_instructions.insert(combined_instructions.end(), instructions.begin(), instructions.end());
    }

    return combined_instructions;
}

template <typename T>
const ProgramMapperArguments &ProgramMapper<T>::getArguments() const
{
    return arguments;
}

template <typename T>
void ProgramMapper<T>::setArguments(const ProgramMapperArguments &newArguments)
{
    arguments = newArguments;
}

} // namespace pisa
