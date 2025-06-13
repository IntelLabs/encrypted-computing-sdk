// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "pisa_graph_optimizer.h"

PISAGraphOptimizer::PISAGraphOptimizer()
{
}

std::vector<pisa::PISAInstruction *> PISAGraphOptimizer::generateInstructionStreamFromGraph(graph::Graph<pisa::PISAInstruction> &p_isa_graph, bool fixed_order, std::vector<pisa::PISAInstruction *> instr_order)
{
    if (fixed_order == false)
    {
        auto instruction_graph = p_isa_graph.clone();

        auto all_nodes = instruction_graph.getNodes();
        for (auto node : all_nodes)
        {
            if (node.GetDat().type != graph::OPERATION)
            {
                instruction_graph.removeNodeMaintainConnections(node);
            }
        }

        auto instruction_graph_consumable = instruction_graph.clone();

        std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> input_layers;
        //Layer peel
        while (instruction_graph_consumable.getNodeCount() > 0)
        {
            auto inputs = instruction_graph_consumable.getInputNodes();
            //input_layers.push_back(inputs);
            std::vector<graph::NetworkNode<pisa::PISAInstruction>> layer;
            for (auto &node : inputs)
            {

                layer.push_back(instruction_graph.getNode(node.GetId()));
                //std::cout << *node.GetDat().instruction << std::endl;
                instruction_graph_consumable.removeNode(node);
                //std::cout << *node.GetDat().instruction << std::endl;
            }
            input_layers.push_back(layer);
        }

        if (perform_variable_isolation)
        {
            isolateGraphVariables(p_isa_graph, input_layers);
        }

        std::vector<pisa::PISAInstruction *> instructions;

        for (auto &layer : input_layers)
        {
            for (auto &node : layer)
            {
                //std::cout << *node.GetDat().instruction << std::endl;
                instructions.push_back(node.GetDat().instruction);
            }
        }
        return instructions;
    }
    else
    {
        return instr_order;
    }
}

void PISAGraphOptimizer::isolateGraphVariables(graph::Graph<pisa::PISAInstruction> &p_isa_graph, std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> &input_layers)
{
    //Generate rename black list
    for (auto &layer : input_layers)
    {
        for (auto &node : layer)
        {
            nodeLocklist(node, p_isa_graph);
        }
    }

    //Adjust variables and generate unique node names
    for (auto &layer : input_layers)
    {
        for (auto &node : layer)
        {
            nodeVariableAdjustment(node, p_isa_graph);
        }
    }
    //Correct registers for accumulate ops
    //    for(auto layer = input_layers.rbegin(); layer != input_layers.rend(); layer++){
    //    //for(auto& layer : input_layers.rbegin()) {
    //        for(auto& node : *layer) {
    //            nodeMACVariableAdjustment(node,p_isa_graph);
    //        }
    //    }

    for (auto &layer : input_layers)
    {
        for (auto &node : layer)
        {
            nodeInstructionAdjustment(node, p_isa_graph);
        }
    }

    return;
}

void PISAGraphOptimizer::applyDuplicateInputVariableSeparation(std::vector<pisa::PISAInstruction *> &instr_order)
{
    std::vector<pisa::PISAInstruction *> newOrder;
    for (auto instr : instr_order)
    {
        //Check input for matches
        bool match = false;
        std::pair<int, int> matching_indices;

        if (instr->numInputOperands() == 2)
        {
            auto &operand_0 = instr->getInputOperand(0);
            auto &operand_1 = instr->getInputOperand(1);
            if (operand_0.location() == operand_1.location())
            {
                std::cout << "Duplicate input variable detected" << std::endl;
                match = true;
            }
        }
        else if (instr->numInputOperands() == 3)
        {
            auto &operand_0 = instr->getInputOperand(0);
            auto &operand_1 = instr->getInputOperand(1);
            auto &operand_2 = instr->getInputOperand(2);

            if (operand_0.location() == operand_1.location())
            {
                match            = true;
                matching_indices = std::pair<int, int>(0, 1);
            }
            if (operand_0.location() == operand_2.location())
            {
                match            = true;
                matching_indices = std::pair<int, int>(0, 2);
            }
            if (operand_1.location() == operand_2.location())
            {
                match            = true;
                matching_indices = std::pair<int, int>(1, 2);
            }
        }
        if (match == false)
        {
            newOrder.push_back(instr);
        }
        else
        {
            std::cout << "Duplicate input variable detected" << std::endl;
            auto copy_instr = pisa::instruction::Copy().create();
            copy_instr->setPMD(instr->PMD());
            copy_instr->setResidual(instr->residual());
            copy_instr->addInputOperand(instr->getInputOperand(matching_indices.second));
            auto output_operand = instr->getInputOperand(matching_indices.second);
            output_operand.setLocation("copyA" + output_operand.location());
            copy_instr->addOutputOperand(output_operand);
            newOrder.push_back(copy_instr);
            instr->getInputOperand(matching_indices.second).setLocation(output_operand.location());
            newOrder.push_back(instr);
        }
    }
    instr_order = newOrder;
    return;
}

void PISAGraphOptimizer::nodeLocklist(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph)
{
    auto p_isa_graph_node = p_isa_graph.getNode(node.GetId());
    for (int x = 0; x < p_isa_graph_node.GetOutDeg(); x++)
    {
        auto target_register = p_isa_graph.getNode(p_isa_graph_node.GetOutNId(x));
        //If target register is an output, don't touch it, if not, rename it
        if (target_register.GetOutDeg() == 0 || node.GetDat().instruction->Name() == pisa::instruction::Mac().baseName)
        {
            rename_lock_list[target_register.GetDat().label] = true;
            //std::cout << "Adjusting "  << target_register.GetDat().label << "  to   " << "uid_" + std::to_string(unique_counter++) + "_" << target_register.GetDat().label << std::endl;
            //target_register.GetDat().label = "uid_" + std::to_string(unique_counter++) + "_" + target_register.GetDat().label;
        }
    }
}

void PISAGraphOptimizer::nodeVariableAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph)
{
    //node.GetInDeg()
    //Adjust outputs only
    auto p_isa_graph_node = p_isa_graph.getNode(node.GetId());
    for (int x = 0; x < p_isa_graph_node.GetOutDeg(); x++)
    {
        auto target_register = p_isa_graph.getNode(p_isa_graph_node.GetOutNId(x));
        //If target register is an output, don't touch it, if not, rename it
        if (/*target_register.GetOutDeg() > 0*/ rename_lock_list.count(target_register.GetDat().label) == 0)
        {
            std::cout << "Adjusting " << target_register.GetDat().label << "  to   "
                      << "uid_" + std::to_string(unique_counter++) + "_" << target_register.GetDat().label << std::endl;
            target_register.GetDat().label = "uid_" + std::to_string(unique_counter++) + "_" + target_register.GetDat().label;
        }
    }
}

void PISAGraphOptimizer::nodeMACVariableAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph)
{

    //
    auto p_isa_graph_node = p_isa_graph.getNode(node.GetId());
    //for(int x = 0; x < p_isa_graph_node.GetOutDeg(); x++) {
    if (p_isa_graph_node.GetDat().instruction->Name() == pisa::instruction::Mac().baseName)
    {
        auto target_register_input_reg  = p_isa_graph.getNode(p_isa_graph_node.GetInNId(0));
        auto target_register_output_reg = p_isa_graph.getNode(p_isa_graph_node.GetOutNId(0));
        //If target register is an output, don't touch it, if not, rename it
        //if(target_register.GetOutDeg() > 0) {
        std::cout << "Adjusting Mac Variable registers" << target_register_input_reg.GetDat().label << "  to   " << target_register_output_reg.GetDat().label << std::endl;

        target_register_input_reg.GetDat().label = target_register_output_reg.GetDat().label;
        //}
    }
    //}
}

void PISAGraphOptimizer::nodeInstructionAdjustment(graph::NetworkNode<pisa::PISAInstruction> &node, graph::Graph<pisa::PISAInstruction> &p_isa_graph)
{
    //
    auto p_isa_graph_node = p_isa_graph.getNode(node.GetId());
    // std::cout << "In degree:"
    if (p_isa_graph_node.GetDat().instruction->Name() == pisa::instruction::Muli().baseName)
    {
        std::cout << "Muli instruction" << std::endl;
        auto input_node_0 = p_isa_graph.getNode(p_isa_graph_node.GetInNId(0)).GetDat();
        auto input_node_1 = p_isa_graph.getNode(p_isa_graph_node.GetInNId(1)).GetDat();

        auto &operand_0 = node.GetDat().instruction->getInputOperand(0);
        auto &operand_1 = node.GetDat().instruction->getInputOperand(1);

        std::cout << "Input label" << 0 << ": " << input_node_0.label << " Immediate: " << operand_0.immediate() << std::endl;
        std::cout << "Input label" << 1 << ": " << input_node_1.label << " Immediate: " << operand_1.immediate() << std::endl;
        if (input_node_0.type == graph::IMMEDIATE)
        {
            operand_0.setLocation(input_node_1.label);
            operand_1.setLocation(input_node_0.label);
        }
        else
        {
            operand_0.setLocation(input_node_0.label);
            operand_1.setLocation(input_node_1.label);
        }
    }
    else if (p_isa_graph_node.GetDat().instruction->Name() == pisa::instruction::Mac().baseName)
    {
        std::cout << "Mac instruction" << std::endl;
        auto input_node_0 = p_isa_graph.getNode(p_isa_graph_node.GetInNId(0)).GetDat();
        auto input_node_1 = p_isa_graph.getNode(p_isa_graph_node.GetInNId(1)).GetDat();
        auto input_node_2 = p_isa_graph.getNode(p_isa_graph_node.GetInNId(2)).GetDat();

        auto output_node_0 = p_isa_graph.getNode(p_isa_graph_node.GetOutNId(0)).GetDat();

        auto &operand_0 = node.GetDat().instruction->getInputOperand(0);
        auto &operand_1 = node.GetDat().instruction->getInputOperand(1);
        auto &operand_2 = node.GetDat().instruction->getInputOperand(2);

        auto &output_operand_0 = node.GetDat().instruction->getOutputOperand(0);

        output_operand_0.setLocation(output_node_0.label);
        if (output_node_0.label == input_node_0.label)
        {
            operand_0.setLocation(input_node_0.label);
            operand_1.setLocation(input_node_1.label);
            operand_2.setLocation(input_node_2.label);
        }
        else if (output_node_0.label == input_node_1.label)
        {
            operand_0.setLocation(input_node_1.label);
            operand_1.setLocation(input_node_0.label);
            operand_2.setLocation(input_node_2.label);
        }
        else if (output_node_0.label == input_node_2.label)
        {
            operand_0.setLocation(input_node_2.label);
            operand_1.setLocation(input_node_0.label);
            operand_2.setLocation(input_node_1.label);
        }
        else
        {
            throw std::runtime_error("No match between input and output registers, MAC instruction no valid output!");
        }

        //        std::cout << "Input label" << 0 << ": " << input_node_0.label << " Immediate: " << operand_0.immediate() <<std::endl;
        //        std::cout << "Input label" << 1 << ": " << input_node_1.label << " Immediate: " << operand_1.immediate() <<std::endl;
        //        if(input_node_0.type == graph::IMMEDIATE) {
        //            operand_0.setLocation(input_node_1.label);
        //            operand_1.setLocation(input_node_0.label);
        //        } else {
        //            operand_0.setLocation(input_node_0.label);
        //            operand_1.setLocation(input_node_1.label);
        //        }
    }
    else
    {
        std::cout << "General instruction" << std::endl;
        for (int x = 0; x < p_isa_graph_node.GetInDeg(); x++)
        {
            auto input_label = p_isa_graph.getNode(p_isa_graph_node.GetInNId(x)).GetDat().label;
            std::cout << "Input label" << x << ": " << input_label << " Immediate: " << node.GetDat().instruction->getInputOperand(x).immediate() << std::endl;
            node.GetDat().instruction->getInputOperand(x).setLocation(input_label);
        }
    }
    for (int x = 0; x < p_isa_graph_node.GetOutDeg(); x++)
    {
        auto input_label = p_isa_graph.getNode(p_isa_graph_node.GetOutNId(x)).GetDat().label;
        std::cout << "Output label" << x << ": " << input_label << std::endl;
        node.GetDat().instruction->getOutputOperand(x).setLocation(input_label);
    }

    return;
}
