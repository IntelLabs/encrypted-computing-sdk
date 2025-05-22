// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <chrono>
#include <ctime>
#include <fstream>
#include <random>

#include <common/graph/graph.h>
#include <common/p_isa/p_isa_hardware_models.h>
#include <common/p_isa/p_isa_instructions.h>

namespace pisa::performance {

struct PerformanceReport
{

    std::string report_name;
    int64_t instruction_count           = 0;
    int64_t total_cycles_used           = 0;
    int64_t total_nops_issued           = 0;
    int64_t total_input_memory_read     = 0;
    int64_t total_output_memory_written = 0;
    // Graph analysis
    int64_t total_inputs        = 0;
    int64_t total_outputs       = 0;
    int64_t graph_depth         = 0;
    int64_t graph_average_width = 0;
    int64_t graph_min_width     = 0;
    int64_t graph_max_width     = 0;
    //
    std::vector<std::pair<std::string, pisa::PISAInstruction *>> schedule_timeline_operation;
    std::vector<std::pair<std::string, pisa::PISAInstruction *>> schedule_timeline_mem_queue;
    void print(std::ostream &output)
    {

        output << report_name << "_Total_cycles: " << total_cycles_used << std::endl;
        output << report_name << "_Total_NOPS: " << total_nops_issued << std::endl;
        output << report_name << "_instructions_per_cycle: " << static_cast<double>(instruction_count) / static_cast<double>(total_cycles_used) << std::endl;
        output << report_name << "_Total_inputs: " << total_inputs << std::endl;
        output << report_name << "_Total_outputs: " << total_outputs << std::endl;
        output << report_name << "_Total_depth: " << graph_depth << std::endl;
        output << report_name << "_Total_avg_width: " << graph_average_width << std::endl;
        output << report_name << "_Total_min_width: " << graph_min_width << std::endl;
        output << report_name << "_Total_max_width: " << graph_max_width << std::endl;
        return;
    }
    void outputExecutionTimeline(std::ostream &output)
    {
        int timeline = 0;
        for (auto op : schedule_timeline_operation)
        {
            output << timeline << ":" << op.first << std::endl;
            timeline++;
        }
    }
    void outputInstructions(std::ostream &output)
    {
        for (auto op : schedule_timeline_operation)
        {
            if (op.first != "NOP" && op.second != nullptr)
            {
                op.second->setOutputBlock(false);
                output << *op.second << std::endl;
            }
        }
    }
};

enum class SCHEDULE_MODE
{
    in_order,
    random,
    lookahead_5,
    next_best
};

enum class ANALYSIS_TYPE
{
    standard,
    instruction,
    memory
};

struct ScheduleConfig
{
    SCHEDULE_MODE schedule_mode = SCHEDULE_MODE::in_order;
    ANALYSIS_TYPE analysis_type = ANALYSIS_TYPE::standard;
    bool quick_schedule         = true;
};

class PISAPerformanceModeler
{
public:
    PISAPerformanceModeler();

    void addGraphAnalysis(PerformanceReport &report);
    void createMemoryGraph(graph::Graph<pisa::PISAInstruction> &graph);
    void createInstructionGraph(graph::Graph<pisa::PISAInstruction> &graph);

    //Update all instructions to use memory node address offsets
    void updateInstructionsToUniqueIntermediateRegisters();
    void updateInstructionsToUniqueIntermediateRegistersNew();
    void generateAndPrintPerformanceReport(PerformanceModels::PISAHardwareModel model = pisa::PerformanceModels::ExampleHardware());
    void generatePerformanceReport(pisa::PerformanceModels::PISAHardwareModel hardware_model);

    PerformanceReport generateInstructionAndMemoryPerformanceGraphReport(ScheduleConfig config, pisa::PerformanceModels::PISAHardwareModel hardware_model);
    void generatePerformanceReportGraph();
    pisa::PerformanceModels::InstructionPerfCharacteristics getMemoryPerformance(graph::NetworkNode<pisa::PISAInstruction> &mem, int current_clock, pisa::PerformanceModels::PISAHardwareModel hardware_model);
    void setInstructionStream(std::vector<pisa::PISAInstruction *> instructions);

private:
    pisa::PerformanceModels::PISAHardwareModel m_hardware_model;

    std::map<std::string, uint> m_instruction_instance_count;
    std::vector<pisa::PISAInstruction *> m_instructions;
};

} // namespace pisa::performance
