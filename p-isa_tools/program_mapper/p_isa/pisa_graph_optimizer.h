// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <common/graph/graph.h>
#include <common/p_isa/p_isa.h>
#include <vector>

class PISAGraphOptimizer
{
public:
    PISAGraphOptimizer();
    std::vector<pisa::PISAInstruction *> generateInstructionStreamFromGraph(graph::Graph<pisa::PISAInstruction> &p_isa_graph, bool fixed_order, std::vector<pisa::PISAInstruction *> instr_order);

    void isolateGraphVariables(graph::Graph<pisa::PISAInstruction> &p_isa_graph, std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> &layers);

    void applyDuplicateInputVariableSeparation(std::vector<pisa::PISAInstruction *> &instr_order);

    void nodeLocklist(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph);
    void nodeVariableAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph);
    void nodeMACVariableAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph);

    void nodeInstructionAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph);
    //void setNodeHeights(graph::Graph<pisa::PISAInstruction>& p_isa_graph);
    //int getNodeHeight(graph::NetworkNode<pisa::PISAInstruction>& node, graph::Graph<pisa::PISAInstruction> p_isa_graph)

    int unique_counter              = 1;
    bool perform_variable_isolation = false;
    std::map<std::string, bool> rename_lock_list;
};
