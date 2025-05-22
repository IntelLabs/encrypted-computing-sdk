// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "p_isa_performance_modeler.h"

using namespace pisa::performance;

PISAPerformanceModeler::PISAPerformanceModeler()
{
}

void PISAPerformanceModeler::addGraphAnalysis(PerformanceReport &report)
{
    auto p_isa_graph_combined     = graph::Graph<pisa::PISAInstruction>::createGraph(m_instructions);
    auto p_isa_graph_instructions = graph::Graph<pisa::PISAInstruction>::createGraph(m_instructions);
    createInstructionGraph(p_isa_graph_instructions);
    auto input           = p_isa_graph_combined.getInputNodes();
    report.total_inputs  = input.size();
    auto output          = p_isa_graph_combined.getOutputNodes();
    report.total_outputs = output.size();

    int depth              = 0;
    report.graph_min_width = 999999;
    report.graph_max_width = 0;

    while (p_isa_graph_instructions.getNodeCount() > 0)
    {
        depth++;
        auto input_nodes       = p_isa_graph_instructions.getInputNodes(true, true, true);
        report.graph_min_width = std::min(report.graph_min_width, (int64_t)input_nodes.size());
        report.graph_max_width = std::max(report.graph_max_width, (int64_t)input_nodes.size());
        report.graph_average_width += input_nodes.size();
        for (auto &input : input_nodes)
        {
            p_isa_graph_instructions.removeNodeMaintainConnections(input);
        }
    }
    report.graph_depth = depth;
    if (depth > 0)
    {
        report.graph_average_width = report.graph_average_width / report.graph_depth;
    }
    return;
}

void PISAPerformanceModeler::createMemoryGraph(graph::Graph<pisa::PISAInstruction> &graph)
{
    auto all_nodes = graph.getNodes();
    for (auto node : all_nodes)
    {
        if (node.GetDat().type == graph::OPERATION)
        {
            graph.removeNodeMaintainConnections(node);
        }
    }
}

void PISAPerformanceModeler::createInstructionGraph(graph::Graph<pisa::PISAInstruction> &graph)
{
    auto all_nodes = graph.getNodes();
    for (auto node : all_nodes)
    {
        if (node.GetDat().type != graph::OPERATION)
        {
            graph.removeNodeMaintainConnections(node);
        }
    }
}

void PISAPerformanceModeler::updateInstructionsToUniqueIntermediateRegisters()
{
    auto p_isa_graph_main = graph::Graph<pisa::PISAInstruction>::createGraph(m_instructions);
    auto p_isa_graph      = p_isa_graph_main.clone();
    auto all_nodes        = p_isa_graph.getNodes();

    //std::cout << "Classify memory nodes" << std::endl;
    // Classify memory types
    for (auto &instr_node : all_nodes)
    {
        if (instr_node.GetDat().type != graph::OPERATION && instr_node.GetInDeg() != 0 && instr_node.GetOutDeg() != 0)
        {
            // Check for restricted instructions to not rename operations
            bool restricted = false;
            for (int x = 0; x < instr_node.GetInDeg(); x++)
            {
                auto node_id = instr_node.GetInNId(x);
                auto node    = p_isa_graph.getNode(node_id);
                if (node.GetDat().instruction->Name() == "mac")
                    restricted = true;
            }

            for (int x = 0; x < instr_node.GetOutDeg(); x++)
            {
                auto node_id = instr_node.GetOutNId(x);
                auto node    = p_isa_graph.getNode(node_id);
                if (node.GetDat().instruction->Name() == "mac")
                    restricted = true;
            }

            if (restricted == false)
            {
                std::string new_node_name = "uid" + std::to_string(instr_node.GetDat().ID) + instr_node.GetDat().label;
                for (int x = 0; x < instr_node.GetInDeg(); x++)
                {
                    auto node_id = instr_node.GetInNId(x);
                    auto node    = p_isa_graph.getNode(node_id);
                    for (int y = 0; y < node.GetDat().instruction->numOutputOperands(); y++)
                    {
                        if (instr_node.GetDat().label == node.GetDat().instruction->getOutputOperand(y).location())
                        {
                            node.GetDat().instruction->getOutputOperand(y).setLocation(new_node_name);
                        }
                    }
                }
                for (int x = 0; x < instr_node.GetOutDeg(); x++)
                {
                    auto node_id = instr_node.GetOutNId(x);
                    auto node    = p_isa_graph.getNode(node_id);
                    for (int y = 0; y < node.GetDat().instruction->numInputOperands(); y++)
                    {
                        if (instr_node.GetDat().label == node.GetDat().instruction->getInputOperand(y).location())
                        {
                            node.GetDat().instruction->getInputOperand(y).setLocation(new_node_name);
                        }
                    }
                }
            }
        }
    }
}

void PISAPerformanceModeler::updateInstructionsToUniqueIntermediateRegistersNew()
{
    auto p_isa_graph_main = graph::Graph<pisa::PISAInstruction>::createGraph(m_instructions);
    auto p_isa_graph      = p_isa_graph_main.clone();
    auto all_nodes        = p_isa_graph.getNodes();

    // First generate set of all nodes with shared mem addresses
    std::map<std::string, std::vector<graph::NetworkNode<pisa::PISAInstruction>>> memory_node_histogram;
    for (auto &instr_node : all_nodes)
    {
        if (instr_node.GetDat().type != graph::OPERATION)
        {
            memory_node_histogram[instr_node.GetDat().label].push_back(instr_node);
        }
    }

    //Print out histogram
    for (auto name : memory_node_histogram)
    {
        std::cout << "Location:" << name.first << " : " << name.second.size() << std::endl;
    }

    int uid_index = 0;
    for (auto &name : memory_node_histogram)
    {
        if (name.second.size() > 1)
        {
            bool needs_rename   = true;
            bool started_rename = false;
            while (name.second.size() > 0 && needs_rename)
            {
                auto &first_node = name.second.front();
                //name.second.pop_back();
                int min_dependency_size = 999999999;
                int max_dependency_size = 0;
                int max_id              = -1;
                for (auto hdnode : name.second)
                {
                    auto depend_graph = p_isa_graph.getNodeDependencyGraph(hdnode.GetId(), false, true);
                    std::vector<graph::NetworkNode<pisa::PISAInstruction>> dependent_nodes;
                    //dependent_nodes.push_back(first_node);

                    auto dependency_nodes = depend_graph.getNodes();
                    std::cout << "Size of dependency graph: " << dependency_nodes.size() << std::endl;
                    if (dependency_nodes.size() < min_dependency_size)
                    {
                        min_dependency_size = dependency_nodes.size();
                        max_id              = hdnode.GetId();
                    }
                }

                auto depend_graph = p_isa_graph.getNodeDependencyGraph(max_id, false, true);
                std::vector<graph::NetworkNode<pisa::PISAInstruction>> dependent_nodes;
                //dependent_nodes.push_back(first_node);

                auto dependency_nodes = depend_graph.getNodes();
                std::cout << "Size of dependency graph: " << dependency_nodes.size() << std::endl;

                for (auto &depend_node : dependency_nodes)
                {
                    if (depend_node.GetDat().label == first_node.GetDat().label)
                    {
                        dependent_nodes.push_back(depend_node);
                    }
                }

                std::cout << "Found difference in nodes for: " << name.first << std::endl;
                std::cout << "Dependent nodes: " << dependent_nodes.size() << "    Histogram nodes: " << name.second.size() << std::endl;
                if (dependent_nodes.size() != name.second.size() || started_rename)
                {
                    started_rename = true;
                    // Create new histogram list
                    std::vector<graph::NetworkNode<pisa::PISAInstruction>> new_histogram;

                    for (auto &node : name.second)
                    {
                        bool is_dependent = false;
                        for (auto hnode : dependent_nodes)
                        {
                            if (node.GetId() == hnode.GetId())
                            {
                                is_dependent = true;
                                std::cout << "Node is a dependent : " << node.GetId() << "  :  " << hnode.GetId() << std::endl;
                            }
                        }
                        if (is_dependent == false)
                        {
                            new_histogram.push_back(node);
                        }
                    }
                    std::cout << "New histogram size: " << new_histogram.size() << std::endl;
                    memory_node_histogram[name.first] = new_histogram;

                    //Update label
                    for (auto &unode : dependent_nodes)
                    {
                        std::string core_name = unode.GetDat().label;
                        std::cout << "Core name:" << core_name << std::endl;
                        std::string updated_name = "uid" + std::to_string(uid_index) + unode.GetDat().label;
                        //Update instr input/output to new label
                        for (int x = 0; x < unode.GetInDeg(); x++)
                        {
                            auto node_id = unode.GetInNId(x);
                            auto node    = p_isa_graph.getNode(node_id);
                            for (int y = 0; y < node.GetDat().instruction->numOutputOperands(); y++)
                            {
                                if (node.GetDat().instruction->getOutputOperand(y).location().length() >= core_name.size())
                                {
                                    std::string core_name_comp = node.GetDat().instruction->getOutputOperand(y).location().substr(node.GetDat().instruction->getOutputOperand(y).location().length() - core_name.size(),
                                                                                                                                  core_name.size());
                                    std::cout << "core name comp  " << core_name_comp << std::endl;
                                    if (core_name == core_name_comp)
                                    {
                                        node.GetDat().instruction->getOutputOperand(y).setLocation(updated_name);
                                    }
                                }
                            }
                            //                                for(int y = 0; y < node.GetDat().instruction->numInputOperands(); y++) {
                            //                                    if(unode.GetDat().label == node.GetDat().instruction->getInputOperand(y).location()) {
                            //                                        node.GetDat().instruction->getInputOperand(y).setLocation(updated_name);
                            //                                    }
                            //                                }
                        }
                        for (int x = 0; x < unode.GetOutDeg(); x++)
                        {
                            auto node_id = unode.GetOutNId(x);
                            auto node    = p_isa_graph.getNode(node_id);
                            for (int y = 0; y < node.GetDat().instruction->numInputOperands(); y++)
                            {
                                if (node.GetDat().instruction->getInputOperand(y).location().length() >= core_name.size())
                                {
                                    std::string core_name_comp = node.GetDat().instruction->getInputOperand(y).location().substr(node.GetDat().instruction->getInputOperand(y).location().length() - core_name.size(),
                                                                                                                                 core_name.size());

                                    std::cout << "core name comp  " << core_name_comp << std::endl;
                                    if (core_name == core_name_comp)
                                    {
                                        node.GetDat().instruction->getInputOperand(y).setLocation(updated_name);
                                    }
                                }
                            }
                            //                                for(int y = 0; y < node.GetDat().instruction->numOutputOperands(); y++) {
                            //                                    if(unode.GetDat().label == node.GetDat().instruction->getOutputOperand(y).location()) {
                            //                                        node.GetDat().instruction->getOutputOperand(y).setLocation(updated_name);
                            //                                    }
                            //                                }
                        }

                        //Update reg label
                        auto pnode = p_isa_graph.getNode(unode.GetId());
                        std::cout << "Updated: " << pnode.GetDat().label << "   to   " << ("uid" + std::to_string(uid_index) + pnode.GetDat().label) << std::endl;
                        pnode.GetDat().label = updated_name;
                    }
                    uid_index++;
                }
                else
                {
                    needs_rename = false;
                }
            }
        }
    }

    auto output = p_isa_graph.getOutputNodes();

    std::cout << "Output nodes after modification: " << std::endl;
    for (auto &x : output)
    {
        std::cout << x.GetDat().label << std::endl;
    }

    p_isa_graph.renderGraphToPNGDot("new_dependent.png", graph::NAME);

    return;
}

void PISAPerformanceModeler::generateAndPrintPerformanceReport(pisa::PerformanceModels::PISAHardwareModel model)
{

    //#TODO: This is currently not functional and under development.
    // Instruction register name rewriting rules. Attempts to identify distinct sets of registers which share a name but are used
    // independently by different sections of the execution graph so that they can be rewritten to allow for safe parallel
    // execution without name conflicts.
    if (false)
    {
        updateInstructionsToUniqueIntermediateRegistersNew();
    }

    std::cout << "Total_Instruction_count: " << m_instructions.size() << std::endl;

    for (auto x : m_instruction_instance_count)
    {
        std::cout << "op_" << x.first << "_Instances: " << x.second << std::endl;
    }
    std::cout << std::endl;

    int64_t min_cycle_time = 99999999999999;
    int64_t max_cycle_time = 0;
    int64_t avg_cycle_time = 0;
    PerformanceReport best_found;
    std::srand(std::time(0));
    ScheduleConfig config;
    for (int x = 0; x < 1; x++)
    {
        auto report_standard = generateInstructionAndMemoryPerformanceGraphReport(config, model);
        if (report_standard.total_cycles_used < min_cycle_time)
        {
            best_found = report_standard;
        }
        min_cycle_time = std::min(min_cycle_time, report_standard.total_cycles_used);
        max_cycle_time = std::max(max_cycle_time, report_standard.total_cycles_used);
        avg_cycle_time += report_standard.total_cycles_used;
    }

    best_found.instruction_count = m_instructions.size();
    addGraphAnalysis(best_found);
    best_found.report_name = "Combined";
    std::cout << "Min cycles:" << min_cycle_time << std::endl;
    std::cout << "Max cycles:" << max_cycle_time << std::endl;
    std::cout << "Avg cycles:" << avg_cycle_time / 1.0 << std::endl;
    best_found.print(std::cout);

    //best_found.outputExecutionTimeline(std::cout);
    if (false)
    {
        auto file = std::ofstream("instructions.txt");
        best_found.outputInstructions(file);
        for (auto instr : m_instructions)
        {
            instr->setOutputBlock(false);
            file << *instr << std::endl;
        }
        file.close();
    }
}

void PISAPerformanceModeler::generatePerformanceReport(pisa::PerformanceModels::PISAHardwareModel hardware_model)
{
    PerformanceReport report;
    for (auto instr : m_instructions)
    {
        report.total_cycles_used += hardware_model.ISAInstructionPerformanceMap[instr->Name()].throughput;
    }

    std::cout << "Total cycles used: " << report.total_cycles_used << std::endl;
}

PerformanceReport PISAPerformanceModeler::generateInstructionAndMemoryPerformanceGraphReport(ScheduleConfig config, pisa::PerformanceModels::PISAHardwareModel hardware_model)
{
    try
    {
        PerformanceReport report;

        auto p_isa_graph_main = graph::Graph<pisa::PISAInstruction>::createGraph(m_instructions);
        auto p_isa_graph      = p_isa_graph_main.clone();
        auto all_nodes        = p_isa_graph.getNodes();

        //std::cout << "Classify memory nodes" << std::endl;
        // Classify memory types
        for (auto &mem_node : all_nodes)
        {
            if (mem_node.GetDat().type != graph::OPERATION)
            {
                if (mem_node.GetInDeg() == 0 || mem_node.GetOutDeg() == 0)
                {
                    mem_node.GetDat().memory_classification = "MEMORY_CACHE";
                }
                else
                {
                    mem_node.GetDat().memory_classification = "REGISTER";
                }
            }
        }

        if (config.analysis_type == ANALYSIS_TYPE::instruction)
        {
            createInstructionGraph(p_isa_graph);
        }
        else if (config.analysis_type == ANALYSIS_TYPE::memory)
        {
            createMemoryGraph(p_isa_graph);
        }
        //p_isa_graph.printGraphInfo();

        auto input_nodes = p_isa_graph.getInputNodes(true, true, true);

        bool use_separate_queues = false;
        //Instructions
        {
            uint64_t instruction_queue_clock = 0;
            uint64_t memory_queue_clock      = 0;
            uint64_t system_clock            = 0;

            uint64_t current_finish_time   = 0;
            uint64_t memory_access_counter = 0;

            while (p_isa_graph.getNodeCount() > 0)
            {

                //Remove any nodes that are complete from input
                {

                    //auto input_nodes = p_isa_graph.getInputNodes(true, true, true);
                    //std::cout << "Input nodes size: " << input_nodes.size() << std::endl;
                    auto input = input_nodes.begin();
                    while (input != input_nodes.end())
                    {
                        if (input->GetDat().scheduled && input->GetDat().end_time <= system_clock)
                        {
                            //std::cout << "Attempting node removal" << std::endl;
                            p_isa_graph.removeNodeMaintainConnections(*input);
                            input = input_nodes.erase(input);
                            // std::cout << "Removal finished" << std::endl;
                        }
                        //std::cout << input.
                        if (input != input_nodes.end())
                            input++;
                    }
                    //std::cout << "Finished node remove" << std::endl;
                }

                //Schedule a new node for execution if possible
                {
                    // bool instruction_scheduled = false;
                    //std::cout << "Refreshing input nodes:" << input_nodes.size() << std::endl;
                    if (input_nodes.size() < 2)
                    {
                        //std::cout << "Nodes zero, refreshing" << std::endl;
                        input_nodes = p_isa_graph.getInputNodes(true, true, true);
                    }
                    else if (config.quick_schedule)
                    {
                        //std::cout << "No fast schedule, refreshing" << std::endl;
                        input_nodes = p_isa_graph.getInputNodes(true, true, true);
                    }

                    //Shuffle order if using random schedule
                    if (config.schedule_mode == SCHEDULE_MODE::random)
                        std::random_shuffle(input_nodes.begin(), input_nodes.end());

                    bool instr_scheduled = false;
                    bool mem_scheduled   = false;
                    //use_separate_queues
                    for (auto &input : input_nodes)
                    {
                        if (input.GetDat().scheduled == false)
                        {

                            if (input.GetDat().type == graph::OPERATION)
                            {

                                if (instruction_queue_clock <= system_clock)
                                {
                                    auto instr_perf           = hardware_model.ISAInstructionPerformanceMap[input.GetDat().instruction->Name()];
                                    input.GetDat().start_time = system_clock;
                                    input.GetDat().end_time   = system_clock + instr_perf.latency;
                                    input.GetDat().scheduled  = true;

                                    instruction_queue_clock += instr_perf.throughput;
                                    system_clock += instr_perf.throughput - 1;
                                    for (int x = 1; x < instr_perf.throughput; x++)
                                    {
                                        report.schedule_timeline_operation.push_back(std::pair<std::string, pisa::PISAInstruction *>("NOP", nullptr));
                                    }

                                    for (int x = 0; x < input.GetOutDeg(); x++)
                                    {
                                        auto output_node                      = p_isa_graph.getNode(input.GetOutNId(x));
                                        output_node.GetDat().last_access_time = memory_access_counter;
                                    }
                                    instr_scheduled = true;
                                }
                            }
                            else
                            {
                                if (memory_queue_clock <= system_clock)
                                {
                                    input.GetDat().start_time = system_clock;
                                    pisa::PerformanceModels::InstructionPerfCharacteristics mem_perf;
                                    if (true)
                                    {
                                        mem_perf = getMemoryPerformance(input, memory_access_counter, hardware_model);
                                    }
                                    else
                                    {
                                        mem_perf = hardware_model.ISAInstructionMemoryMap[input.GetDat().memory_classification];
                                    }

                                    memory_access_counter++;

                                    input.GetDat().end_time  = system_clock + mem_perf.latency;
                                    input.GetDat().scheduled = true;
                                    memory_queue_clock += mem_perf.throughput;
                                    system_clock += mem_perf.throughput - 1;
                                    for (int x = 1; x < mem_perf.throughput; x++)
                                    {
                                        report.schedule_timeline_mem_queue.push_back(std::pair<std::string, pisa::PISAInstruction *>("NOP", nullptr));
                                    }
                                    mem_scheduled = true;
                                }
                            }
                            if (input.GetDat().scheduled == true)
                            {
                                report.total_cycles_used = current_finish_time;
                                current_finish_time      = input.GetDat().end_time;
                                //instruction_scheduled    = true;
                                report.schedule_timeline_operation.push_back(std::pair<std::string, pisa::PISAInstruction *>(input.GetDat().label, input.GetDat().instruction));
                            }
                            if (instr_scheduled && mem_scheduled)
                                break;
                        }
                    }
                    if (instr_scheduled == false)
                    {
                        report.schedule_timeline_operation.push_back(std::pair<std::string, pisa::PISAInstruction *>("NOP", nullptr));
                        report.total_nops_issued++;
                    }
                    if (mem_scheduled == false)
                    {
                        report.schedule_timeline_mem_queue.push_back(std::pair<std::string, pisa::PISAInstruction *>("NOP", nullptr));
                    }
                    system_clock++;
                }
            }
        }

        return report;
    }
    catch (...)
    {
        std::cout << "Crash during perf analysis" << std::endl;
        throw;
    }
}

void PISAPerformanceModeler::generatePerformanceReportGraph()
{
    PerformanceReport report;
}

pisa::PerformanceModels::InstructionPerfCharacteristics PISAPerformanceModeler::getMemoryPerformance(graph::NetworkNode<pisa::PISAInstruction> &mem, int current_clock, pisa::PerformanceModels::PISAHardwareModel hardware_model)
{
    pisa::PerformanceModels::InstructionPerfCharacteristics perf;

    if (mem.GetDat().memory_classification == "MEMORY_CACHE")
    {
        perf = hardware_model.ISAInstructionMemoryMap["MEMORY_CACHE"];
    }
    else if (current_clock - mem.GetDat().last_access_time < hardware_model.MemorySizesMap["REGISTER"])
    {
        perf = hardware_model.ISAInstructionMemoryMap["REGISTER"];
    }
    else if (current_clock - mem.GetDat().last_access_time < hardware_model.MemorySizesMap["CACHE"])
    {
        perf = hardware_model.ISAInstructionMemoryMap["CACHE"];
    }
    else
    {
        perf = hardware_model.ISAInstructionMemoryMap["MEMORY_CACHE"];
    }

    mem.GetDat().last_access_time = current_clock;

    return perf;
}

void PISAPerformanceModeler::setInstructionStream(std::vector<pisa::PISAInstruction *> instructions)
{
    for (auto instr : instructions)
    {
        m_instruction_instance_count[instr->Name()]++;
        this->m_instructions.push_back(instr);
    }
}
