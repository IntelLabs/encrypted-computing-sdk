// Copyright (C) 2023 Intel Corporation

#pragma once

#include <filesystem>
#include <map>
#include <memory>
#include <iostream>
#include <unordered_set>

#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <program_mapper/poly_program/polyprogram.h>

namespace pisa::kernel {

class Cache
{
public:
    Cache() = delete;
    Cache(const std::string &dirname, bool use_cache = true, bool remove_cache = false) :
        _dirname(dirname), _use_cache(use_cache), _remove_cache(remove_cache)
    {
        std::filesystem::create_directory(_dirname);
    }

    std::string getDirname() const { return _dirname; }
    bool use_cache() const { return _use_cache; }

    ~Cache()
    {
        if (_remove_cache)
        {
            std::filesystem::remove_all(_dirname);
        }
    }

private:
    std::string _dirname;
    bool _use_cache;
    bool _remove_cache;
};

class PISAKernel
{
public:
    PISAKernel() = default;
    PISAKernel(const std::vector<std::string> &input_names_,
               const std::vector<std::string> &output_names_,
               const std::vector<std::string> &immediate_names_ = {}) :
        input_names(input_names_),
        output_names(output_names_),
        immediate_names(immediate_names_)
    {
    }

    static PISAKernel *create(std::string he_op_generator, pisa::poly::PolyOperation *op, const Cache &kernel_cache, bool verbose = false, bool new_kerngen = false, std::string kern_library = "CSV");

    static PISAKernel *create_legacy(std::string he_op_generator, pisa::poly::PolyOperation *op, const Cache &kernel_cache, bool verbose = false);
    static PISAKernel *create_new(std::string he_op_generator, pisa::poly::PolyOperation *op, const Cache &kernel_cache, bool verbose = false);

    static PISAKernel *createHECDataFormats(std::string he_op_generator, pisa::poly::PolyOperation *op, const Cache &kernel_cache, bool verbose = false);

    virtual PISAKernel *createInstance() { return new PISAKernel(); }
    std::vector<pisa::PISAInstruction *> instructions;
    std::vector<pisa::PISAInstruction *> mapped_instructions;

    std::vector<std::string> input_names;
    std::vector<std::string> output_names;
    std::vector<std::string> immediate_names;

    bool map_dirty = true;

    void updateInput(int index, std::string new_name);
    void updateOutput(int index, std::string new_name);
    void updateSymbols(bool verbose = false);

    std::map<std::string, std::string> naming_map;
    std::map<std::string, std::string> immediate_map;

    void setImmediate(const std::string &, const std::string &);
    void mapInput(int index, const std::string &new_name);
    void mapImmediate(int index, const std::string &new_name);
    void mapOutput(int index, const std::string &new_name);
    const std::vector<pisa::PISAInstruction *> &getMappedInstructions();

    void createInternalVariableMap();
    void determineVariableNamingViaGraph();
    std::map<std::string, std::string> internal_map;

    std::string name;
    unsigned int kernel_id;

    bool enable_namespace = true;
    bool enableNamespace() const;
    void setEnableNamespace(bool newNamespace_internal_variables);

    /**
     * @brief registerNameRoot Attempts to split a register name removing the RNS and block terms.
     * @todo Need to account for outlier cases when naming doesn't match
     * @param location
     * @return
     */
    std::string registerNameRoot(const std::string &reg_name);

    std::vector<std::string> nonRepeatingRootsNode(std::vector<graph::NetworkNode<pisa::PISAInstruction>> &xputs);
    const std::vector<std::string> &getInput_names() const;
    const std::vector<std::string> &getOutput_names() const;
};

} // namespace pisa::kernel
