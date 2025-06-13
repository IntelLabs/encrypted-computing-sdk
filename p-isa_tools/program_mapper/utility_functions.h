// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

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

using DATA_TYPE = uint32_t;
namespace fs    = std::filesystem;

std::vector<std::string> generateMemFile(const graph::Graph<pisa::PISAInstruction> &graph, int max_rns_terms)
{
    const auto inputs  = graph.getInputNodes(true, false);
    const auto outputs = graph.getOutputNodes();

    int counter                          = 0;
    std::vector<std::string> memory_file = {
        "dload, ntt_auxiliary_table, " + std::to_string(counter++),
        "dload, ntt_routing_table, " + std::to_string(counter++),
        "dload, intt_auxiliary_table, " + std::to_string(counter++),
        "dload, intt_routing_table, " + std::to_string(counter++)
    };

    // Get twid/ones iterations
    int high_rns_iters = 1 + ((max_rns_terms - 1) / 64);

    //Add preamble strings
    std::generate_n(std::back_inserter(memory_file), 8 * high_rns_iters, [&counter]() {
        return "dload, twid, " + std::to_string(counter++);
    });
    std::generate_n(std::back_inserter(memory_file), high_rns_iters, [&counter]() {
        return "dload, ones, " + std::to_string(counter++);
    });

    //Add inputs
    std::map<std::string, int> hbm_address_map;
    std::transform(inputs.begin(), inputs.end(), std::back_inserter(memory_file),
                   [&counter, &hbm_address_map](const auto &x) {
                       if (hbm_address_map.count(x.GetDat().label) == 0)
                       {
                           hbm_address_map[x.GetDat().label] = counter++;
                       }
                       return "dload, poly, " + std::to_string(hbm_address_map[x.GetDat().label]) + ", " + x.GetDat().label;
                   });

    //Add outputs
    std::transform(outputs.begin(), outputs.end(), std::back_inserter(memory_file),
                   [&counter, &hbm_address_map](const auto &x) {
                       //dstore, output_0_0_0, 73
                       if (hbm_address_map.count(x.GetDat().label) == 0)
                       {
                           hbm_address_map[x.GetDat().label] = counter++;
                       }
                       return "dstore, " + x.GetDat().label + ", " + std::to_string(hbm_address_map[x.GetDat().label]);
                   });

    return memory_file;
}
/**
 * @brief registerNameRoot Attempts to split a register name removing the RNS and block terms.
 * @todo Need to account for outlier cases when naming doesn't match
 * @param location
 * @return
 */
inline std::string registerNameRoot(const std::string &reg_name)
{
    int size = reg_name.find('_', 0);
    return reg_name.substr(0, size);
}

template <typename T>
inline std::vector<std::string> nonRepeatingRoots(const T &xputs)
{
    std::vector<std::string> roots;
    roots.reserve(xputs.size());
    std::transform(xputs.begin(), xputs.end(), std::back_inserter(roots),
                   [](const auto &xput) {
                       const auto &root = registerNameRoot(xput.first);
                       return root;
                   });
    // removes consecutive (adjacent) duplicates
    auto it = std::unique(roots.begin(), roots.end());
    roots.erase(it, roots.end());
    return roots;
}

template <typename T>
inline std::vector<std::string> nonRepeatingRootsNode(const T &xputs)
{
    std::vector<std::string> roots;
    roots.reserve(xputs.size());
    std::transform(xputs.begin(), xputs.end(), std::back_inserter(roots),
                   [](const auto &xput) {
                       const auto &root = registerNameRoot(xput.GetDat().label);
                       return root;
                   });
    // removes consecutive (adjacent) duplicates
    auto it = std::unique(roots.begin(), roots.end());
    roots.erase(it, roots.end());
    return roots;
}

/**
 * @brief generateRegisterMap Maps all input/output variable name roots in trace to a map structure. Current structure is 1 : 1
 * @param input_parser_v0
 * @return
 */
inline std::map<std::string, std::string> generateRegisterMap(const JSONDataHandler<DATA_TYPE> &input_parser_v0)
{
    const auto &inputs_v0        = input_parser_v0.getAllInputs();
    const auto &outputs_v0       = input_parser_v0.getAllOutputs();
    const auto &intermediates_v0 = input_parser_v0.getAllIntermediatess();
    auto input_roots             = nonRepeatingRoots(inputs_v0);
    auto output_roots            = nonRepeatingRoots(outputs_v0);
    auto intermediate_roots      = nonRepeatingRoots(intermediates_v0);

    for (const auto &input : inputs_v0)
    {
        std::cout << input.first << '\n';
    }
    std::cout << std::flush;

    std::map<std::string, std::string> register_map;

    for (const auto &root : input_roots)
    {
        register_map[root] = root;
    }

    for (const auto &root : output_roots)
    {
        register_map[root] = root;
    }

    for (const auto &root : intermediate_roots)
    {
        register_map[root] = root;
    }

    return register_map;
}

inline void dumpMapToFile(const std::string &file_name, const std::map<std::string, std::string> &map)
{
    std::ofstream map_file(file_name);
    if (!map_file.is_open())
        throw std::runtime_error("Could not open file '" + file_name + "'.");
    for (const auto &[k, v] : map)
    {
        map_file << k << "," << v << std::endl;
    }
}

template <typename T, typename FN>
inline void writeToFileBy(const std::string &filename, const std::vector<T> &inputs, FN fn)
{
    std::ofstream ofile(filename);
    if (!ofile.is_open())
        throw std::runtime_error("Could not open file '" + filename + "'.");
    for (const auto &input : inputs)
        ofile << fn(input) << '\n';
}
