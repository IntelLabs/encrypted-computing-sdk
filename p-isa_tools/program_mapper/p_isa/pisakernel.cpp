// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <filesystem>
#include <sstream>

#include <common/p_isa/parser/p_isa_parser.h>
#include <program_mapper/p_isa/pisakernel.h>
#include <program_mapper/poly_program/polynomial.h>

namespace pisa::kernel {

const std::vector<std::string> &PISAKernel::getOutput_names() const
{
    return output_names;
}

const std::vector<std::string> &PISAKernel::getInput_names() const
{
    return input_names;
}

static unsigned int global_kernel_id_counter = 0;

} // namespace pisa::kernel

// Helper function for generating the kernel generator input given an operation
inline std::string genKernInput(const pisa::poly::PolyOperation &op)
{
    /*
     * CONTEXT SCHEME poly_order key_rns current_rns
     * DATA    symbol num_parts
     * OPNAME  output input(s)
     */
    std::ostringstream input;
    // CONTEXT
    input << "CONTEXT " << toString(op.parentProgram()->scheme())
          << " " << op.parentProgram()->getPolyModulusDegree()
          << " " << op.parentProgram()->getKeyRns()
          << " " << op.getInputOperand(0).num_of_rns_terms
          << "\n";

    // DATA
    // NOTE: CipherDegree is tied to HEOperation not Operand
    auto operation                             = op.Name();
    std::vector<pisa::poly::Polynomial> inputs = op.getInputLocations();
    std::vector<pisa::poly::Polynomial> output = op.getOutputLocations();

    //#TODO Naming is switched to use generic sequential naming allowing program mapper to control the final naming
    //This allows generic kernels to be generated effectively for the cache, while passing names worked well for single
    //operations it creates issues for multi ops. A more robust fix with runtime control on which naming control scheme to use may be desirable.
    for (int i = 0; i < op.numOutputOperands(); ++i)
    {
        input << "DATA " << /*output[i].register_name*/ "output" << i
              << " " << output[i].num_of_polynomials << "\n";
    }

    for (int i = 0; i < op.numInputOperands(); ++i)
    {
        input << "DATA " << /*inputs[i].register_name*/ "input" << i
              << " " << inputs[i].num_of_polynomials << "\n";
    }

    // OP
    input << std::uppercase << op.Name() << std::nouppercase;
    for (int i = 0; i < op.numOutputOperands(); ++i)
    {
        input << " "
              << "output" << i /*output[i].register_name*/;
    }
    for (int i = 0; i < op.numInputOperands(); ++i)
    {
        input << " "
              << "input" << i /*inputs[i].register_name*/;
    }

    return input.str();
}

// Helper function creating kernel filepath
inline std::filesystem::path createKernelFilepath(const pisa::poly::PolyOperation &op, const pisa::kernel::Cache &kernel_cache)
{
    std::ostringstream kernel_file_name;
    kernel_file_name << toString(op.parentProgram()->scheme()) << "_"
                     << op.Name() << "_"
                     << op.parentProgram()->getPolyModulusDegree() << "_"
                     << op.getInputLocations().front().num_of_polynomials << "_"
                     << op.getInputLocations().front().num_of_rns_terms << ".csv";

    return std::filesystem::path(kernel_cache.getDirname()) / kernel_file_name.str();
}

// Selection function for choosing between legacy and new kernel generators
pisa::kernel::PISAKernel *pisa::kernel::PISAKernel::create(std::string he_op_generator, pisa::poly::PolyOperation *op, const pisa::kernel::Cache &kernel_cache, bool verbose, bool new_kerngen, std::string kern_library)
{
    if (new_kerngen)
    {
        return create_new(he_op_generator, op, kernel_cache, verbose);
    }
    if (kern_library == "CSV")
    {
        return create_legacy(he_op_generator, op, kernel_cache, verbose);
    }
    else if (kern_library == "HDF")
    {
        return createHECDataFormats(he_op_generator, op, kernel_cache, verbose);
    }
    else
        throw std::runtime_error("Invalid kernel library");
}

pisa::kernel::PISAKernel *pisa::kernel::PISAKernel::create_new(std::string he_op_generator, pisa::poly::PolyOperation *op, const pisa::kernel::Cache &kernel_cache, bool verbose)
{
    PISAKernel *kernel = PISAKernel().createInstance();
    kernel->name       = op->Name();
    kernel->kernel_id  = pisa::kernel::global_kernel_id_counter++;

    const auto kernel_file_path      = createKernelFilepath(*op, kernel_cache);
    const std::string command_string = he_op_generator + " -q -l > " + kernel_file_path.c_str() + " <<EOF\n" + genKernInput(*op) + "\nEOF\n";
    if (verbose)
    {
        std::cout << command_string << std::endl;
    }

    if (!kernel_cache.use_cache() || !std::filesystem::exists(kernel_file_path))
    {
        [[maybe_unused]] auto rc = system(command_string.c_str());
    }

    kernel->instructions = pisa::PISAParser::parse(kernel_file_path);
    kernel->mapped_instructions.resize(kernel->instructions.size());
    for (int x = 0; x < kernel->instructions.size(); x++)
        kernel->mapped_instructions[x] = new pisa::PISAInstruction(*kernel->instructions[x]);

    return kernel;
}

pisa::kernel::PISAKernel *pisa::kernel::PISAKernel::create_legacy(std::string he_op_generator, pisa::poly::PolyOperation *op, const pisa::kernel::Cache &kernel_cache, bool verbose)
{
    PISAKernel *kernel = PISAKernel().createInstance();
    kernel->name       = op->Name();
    kernel->kernel_id  = pisa::kernel::global_kernel_id_counter++;

    std::ostringstream params;
    params << toString(op->parentProgram()->scheme(), true) << " "
           << op->Name() << " "
           << std::to_string(op->parentProgram()->getPolyModulusDegree()) << " "
           << op->getInputOperand(0).num_of_rns_terms;

    auto kernel_file_name = params.str() + "_" + std::to_string(op->getInputOperand(0).num_of_polynomials) + ".csv";
    std::replace(kernel_file_name.begin(), kernel_file_name.end(), ' ', '_');

    // Add to correct calling params.
    params << " " << (op->getInputOperand(0).num_of_rns_terms + 1);

    if (op->Name() == "add")
    {
        params << " " << op->getInputOperand(0).num_of_polynomials;
    }

    if (op->Name() == "relin" || op->Name() == "rotate")
    {
        // If passing dnum (number of digits), need to also pass alpha (digit size) and k (size of the extended prime)
        // dnum == rns and alpha/k are 1 as we're using rns-prime decomposition for key switching
        int dnum  = op->getInputOperand(0).num_of_rns_terms;
        int alpha = op->parentProgram()->getAlpha() == 0 ? 1 : op->parentProgram()->getAlpha();
        int k     = alpha;
        params << " " << dnum << " " << alpha << " " << k;
    }

    if (verbose)
    {
        std::cout << he_op_generator << " " << params.str() << std::endl;
    }

    auto kernel_file_path = std::filesystem::path(kernel_cache.getDirname()) / kernel_file_name;
    if (!kernel_cache.use_cache() || !std::filesystem::exists(kernel_file_path))
    {
        std::string command_string = he_op_generator + " " + params.str() + " > " + kernel_file_path.c_str();
        std::cout << command_string << std::endl;
        [[maybe_unused]] auto rc = system(command_string.c_str());
    }

    kernel->instructions = pisa::PISAParser::parse(kernel_file_path);
    kernel->mapped_instructions.resize(kernel->instructions.size());
    for (int x = 0; x < kernel->instructions.size(); x++)
        kernel->mapped_instructions[x] = new pisa::PISAInstruction(*kernel->instructions[x]);

    return kernel;
}

pisa::kernel::PISAKernel *pisa::kernel::PISAKernel::createHECDataFormats(std::string he_op_generator, pisa::poly::PolyOperation *op, const pisa::kernel::Cache &kernel_cache, bool verbose)
{
    PISAKernel *kernel = PISAKernel().createInstance();
    kernel->name       = op->Name();
    kernel->kernel_id  = pisa::kernel::global_kernel_id_counter++;

    std::ostringstream params;
    params << toString(op->parentProgram()->scheme(), true) << " "
           << op->Name() << " "
           << op->parentProgram()->getPolyModulusDegree() << " "
           << op->getRnsTerms();

    int key_rns_num = op->parentProgram()->getKeyRns();
    uint32_t q_size = op->parentProgram()->getQSize();
    int dnum        = op->parentProgram()->getDNum();
    uint32_t alpha  = op->parentProgram()->getAlpha();
    // k = alpha
    int k = alpha;

    params << " " << key_rns_num;

    if (op->Name() == "relin")
    {
        // If passing dnum (number of digits), need to also pass alpha (digit size) and k (size of the extended prime)
        // dnum == rns and alpha/k are 1 as we're using rns-prime decomposition for key switching
        params << " " << dnum << " " << alpha << " " << k << " " << q_size;
    }
    else if (op->Name() == "add")
    {
        params << " " << op->getCipherDegree();
    }
    else if (op->Name() == "rotate")
    {
        // If passing dnum (number of digits), need to also pass alpha (digit size) and k (size of the extended prime)
        // dnum == rns and alpha/k are 1 as we're using rns-prime decomposition for key switching
        params << " " << dnum << " " << alpha << " " << k;
        params << " " << q_size << " " << op->getGaloisElt();
    }
    else if (op->Name() == "rescale")
    {
        // qsize is required for Dataformats CKKS
        params << " " << q_size;
    }
    if (verbose)
    {
        std::cout << he_op_generator << " " << params.str() << std::endl;
    }

    // make kernel_file_name use full params
    auto kernel_file_name = params.str() + "_" + std::to_string(op->getCipherDegree()) + ".csv";
    std::replace(kernel_file_name.begin(), kernel_file_name.end(), ' ', '_');

    auto kernel_file_path = std::filesystem::path(kernel_cache.getDirname()) / kernel_file_name;
    // debugging
    if (!kernel_cache.use_cache() || !std::filesystem::exists(kernel_file_path))
    {
        std::string command_string = he_op_generator + " " + params.str() + " > " + kernel_file_path.c_str();
        std::cout << command_string << std::endl;
        [[maybe_unused]] auto rc = system(command_string.c_str());
    }

    kernel->instructions = pisa::PISAParser::parse(kernel_file_path);
    kernel->mapped_instructions.resize(kernel->instructions.size());
    for (int x = 0; x < kernel->instructions.size(); x++)
        kernel->mapped_instructions[x] = new pisa::PISAInstruction(*kernel->instructions[x]);

    return kernel;
}

bool pisa::kernel::PISAKernel::enableNamespace() const
{
    return enable_namespace;
}

void pisa::kernel::PISAKernel::setEnableNamespace(bool newNamespace_internal_variables)
{
    enable_namespace = newNamespace_internal_variables;
}

std::string pisa::kernel::PISAKernel::registerNameRoot(const std::string &reg_name)
{
    int size = reg_name.find('_', 0);
    return reg_name.substr(0, size);
}

std::vector<std::string> pisa::kernel::PISAKernel::nonRepeatingRootsNode(std::vector<graph::NetworkNode<PISAInstruction>> &xputs)
{
    std::unordered_set<std::string> non_repeat_roots;
    std::vector<std::string> non_repeat_roots_insertion_ordered;
    for (auto xput : xputs)
    {
        auto root = registerNameRoot(xput.GetDat().label);
        if (non_repeat_roots.count(root) == 0)
        {
            non_repeat_roots_insertion_ordered.push_back(root);
        }
        non_repeat_roots.insert(root);
    }
    return non_repeat_roots_insertion_ordered;
}

void pisa::kernel::PISAKernel::updateInput(int index, std::string new_name)
{
    std::string old_name = input_names[index];

    for (auto &i : instructions)
    {
        for (int x = 0; x < i->numInputOperands(); x++)
        {
            auto name_root = i->getInputOperand(x).locationRoot();
            if (name_root == old_name)
            {
                i->getInputOperand(x).setLocationRoot(new_name);
            }
        }
    }
    input_names[index] = new_name;
}

void pisa::kernel::PISAKernel::updateOutput(int index, std::string new_name)
{
    std::string old_name = output_names[index];

    for (auto &i : instructions)
    {
        for (int x = 0; x < i->numOutputOperands(); x++)
        {
            auto name_root = i->getOutputOperand(x).locationRoot();
            if (name_root == old_name)
            {
                i->getOutputOperand(x).setLocationRoot(new_name);
            }
        }
    }
    output_names[index] = new_name;
}

void pisa::kernel::PISAKernel::updateSymbols(bool verbose)
{
    try
    {
        if (internal_map.size() == 0)
            createInternalVariableMap();

        for (int i = 0; i < instructions.size(); i++)
        {
            for (int x = 0; x < instructions[i]->numInputOperands(); x++)
            {
                auto name_root = instructions[i]->getInputOperand(x).locationRoot();
                if (naming_map.count(name_root) == 1)
                {
                    auto value = naming_map[name_root];
                    mapped_instructions[i]->getInputOperand(x).setLocationRoot(value);
                    if (verbose)
                        std::cout << "Mapped: " << name_root << "->" << value << std::endl;
                }
                else if (enable_namespace)
                {
                    auto name_loc = internal_map[instructions[i]->getInputOperand(x).location()];
                    mapped_instructions[i]->getInputOperand(x).setLocation(name_loc);
                    if (verbose)
                        std::cout << "Mapped: " << instructions[i]->getInputOperand(x).location() << "->" << name_loc << std::endl;
                }
            }

            for (int x = 0; x < instructions[i]->numOutputOperands(); x++)
            {
                auto name_root = instructions[i]->getOutputOperand(x).locationRoot();
                if (naming_map.count(name_root) == 1)
                {
                    auto value = naming_map[name_root];
                    mapped_instructions[i]->getOutputOperand(x).setLocationRoot(value);
                    if (verbose)
                        std::cout << "Mapped: " << name_root << "->" << value << std::endl;
                }
                else if (enable_namespace)
                {
                    auto name_loc = internal_map[instructions[i]->getOutputOperand(x).location()];
                    mapped_instructions[i]->getOutputOperand(x).setLocation(name_loc);
                    if (verbose)
                        std::cout << "Mapped: " << instructions[i]->getOutputOperand(x).location() << "->" << name_loc << std::endl;
                }
            }
            map_dirty = false;
        }
    }
    catch (...)
    {
        throw;
    }
}

void pisa::kernel::PISAKernel::setImmediate(const std::string &key, const std::string &value)
{
    immediate_map[key] = value;
    map_dirty          = true;
}

void pisa::kernel::PISAKernel::mapInput(int index, const std::string &new_name)
{
    naming_map[input_names[index]] = new_name;
    map_dirty                      = true;
}

void pisa::kernel::PISAKernel::mapImmediate(int index, const std::string &new_name)
{
    naming_map[immediate_names[index]] = new_name;
    map_dirty                          = true;
}

void pisa::kernel::PISAKernel::mapOutput(int index, const std::string &new_name)
{
    naming_map[output_names[index]] = new_name;
    map_dirty                       = true;
}

const std::vector<pisa::PISAInstruction *> &pisa::kernel::PISAKernel::getMappedInstructions()
{
    if (map_dirty)
        updateSymbols(false);

    return mapped_instructions;
}

void pisa::kernel::PISAKernel::createInternalVariableMap()
{

    for (const auto &meta : immediate_names)
    {
        naming_map[meta]   = meta;
        internal_map[meta] = meta;
    }
    for (auto meta : immediate_map)
    {
        naming_map[meta.first]   = meta.second;
        internal_map[meta.first] = meta.second;
    }

    for (int i = 0; i < instructions.size(); i++)
    {
        for (int x = 0; x < instructions[i]->numInputOperands(); x++)
        {
            auto name_root = instructions[i]->getInputOperand(x).locationRoot();
            auto name_loc  = instructions[i]->getInputOperand(x).location();
            //if(name_root.size() > 0) {
            if (naming_map.count(name_root) == 0 && immediate_map.count(name_loc) == 0 && internal_map.count(name_loc) == 0)
            {
                internal_map[name_loc] = "internal" + name + std::to_string(kernel_id) + "NS_" + name_loc;
            }
        }

        for (int x = 0; x < instructions[i]->numOutputOperands(); x++)
        {
            auto name_loc  = instructions[i]->getOutputOperand(x).location();
            auto name_root = instructions[i]->getOutputOperand(x).locationRoot();
            //if(name_root.size() > 0) {
            if (naming_map.count(name_root) == 0 && immediate_map.count(name_loc) == 0 && internal_map.count(name_loc) == 0)
            {
                internal_map[name_loc] = "internal" + name + std::to_string(kernel_id) + "NS_" + name_loc;
            }
        }
    }
}

bool containsString(const std::string &value, const std::string &substring)
{
    return value.find(substring) != std::string::npos;
}

void pisa::kernel::PISAKernel::determineVariableNamingViaGraph()
{
    auto instruction_graph = graph::Graph<pisa::PISAInstruction>::createGraph(instructions);
    auto inputs            = instruction_graph.getInputNodes(true, false, false);
    auto outputs           = instruction_graph.getOutputNodes();
    auto immediates        = instruction_graph.getInputNodes(false, true, false);

    auto non_repeat_inputs  = nonRepeatingRootsNode(inputs);
    auto non_repeat_outputs = nonRepeatingRootsNode(outputs);
    for (auto &input : non_repeat_inputs)
    {
        input_names.push_back(input);
        naming_map[input] = input;
    }
    // temporary solution for two corner cases:
    // Two inputs are needed but "d" is parsed before "c" causing input1 and input2 being swapped
    // Trace has TWO inputs but only "d" is used, it will cause mapInput function to crash
    // NOTE: This could still lead to an issue for second corner case where only "c" is used but trace has two inputs
    //if (input_names.size() == 1 && input_names.front() == "d")
    //    input_names.push_back("c");
    // std::sort(input_names.begin(), input_names.end(), comp);
    // Attempt #2, just sort inputs if the label contains "input"
    // Leave the rest of the list alone
    // TODO: Generalize Function
    auto comp = [](const std::string &a, const std::string &b) {
        if (containsString(a, "input") && containsString(b, "input"))
            return a < b;
        else
            return false;
    };
    std::sort(input_names.begin(), input_names.end(), comp);

    for (auto &output : non_repeat_outputs)
    {
        output_names.push_back(output);
        naming_map[output] = output;
    }
    std::sort(output_names.begin(), output_names.end());

    for (auto &immediate : immediates)
    {
        if (immediate_map.count(immediate.GetDat().label) == 0)
        {
            immediate_names.push_back(immediate.GetDat().label);
        }
        immediate_map[immediate.GetDat().label] = immediate.GetDat().label;
    }
}
