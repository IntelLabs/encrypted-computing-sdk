// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <map>
#include <type_traits>

#include <Snap.h>

#include <common/p_isa/p_isa.h>

namespace graph {

enum NODE_TYPE
{
    OPERATION,
    REGISTER_ADDRESS,
    IMMEDIATE
};

enum LABEL_OPTION
{
    NAME,
    OUT_STRING,
    ID,
    NONE
};

template <typename INSTRUCTION>
class Node
{
public:
    Node() = default;
    Node(const std::string &_label, int _ID, NODE_TYPE _type, INSTRUCTION *instr = nullptr) :
        ID(_ID),
        type(_type),
        label(_label),
        output_string(label),
        instruction(instr)
    {
    }

    void Save(TSOut &SOut) const {}

    int ID;
    int count;
    NODE_TYPE type;
    std::string memory_classification;
    std::string label;
    std::string output_string;
    INSTRUCTION *instruction;

    //Perf tracking
    bool scheduled       = false;
    int start_time       = -1;
    int end_time         = -1;
    int last_access_time = -1;
};

class Edge
{
public:
    void Save(TSOut &SOut) const {}
    bool operator<(const Edge &b) const
    {
        return name < b.name;
    }

    std::string name;
    int value;
};

template <typename INSTRUCTION>
using NetworkNode = typename TNodeEDatNet<Node<INSTRUCTION>, Edge>::TNodeI;
template <typename INSTRUCTION>
using Network = typename TNodeEDatNet<Node<INSTRUCTION>, Edge>::PNet;

// Wrapper to help with stream operator
template <typename E>
struct with_delimiter
{
    with_delimiter(const std::vector<E> &elements, const std::string &delim) :
        elements_(elements), delimiter_(delim) {}
    const std::vector<E> &elements_;
    const std::string delimiter_;
};

template <typename NODE>
inline std::ostream &operator<<(std::ostream &out, const with_delimiter<NODE> &nodes)
{
    for (const auto &node : nodes.elements_)
    {
        out << node.GetDat().label << nodes.delimiter_;
    }
    return out;
}

template <typename INSTRUCTION>
class Graph
{
public:
    static Graph createGraph(std::vector<INSTRUCTION *> instructions);

    Graph() = default;
    Graph(Graph &graph) :

        network(graph.cloneGraph(graph.network))
    {
    }

    Graph clone() const
    {
        Graph graph;
        graph.network = cloneGraph(network);
        return graph;
    }

    void printGraphInfo() const
    {
        TSnap::PrintInfo(network);
    }

    NetworkNode<INSTRUCTION> getNode(int node_id);
    std::vector<NetworkNode<INSTRUCTION>> getNodes() const;
    std::vector<NetworkNode<INSTRUCTION>> getOutputNodes() const;
    std::vector<NetworkNode<INSTRUCTION>> getInputNodes(bool include_registers = true, bool include_immediates = true, bool include_operations = true) const;
    void removeAllExceptOutputNodes() { getOutputNodesInPlace(network); }
    void removeAllExceptInputNodes() { getInputNodesInPlace(network); }
    void removeNode(NetworkNode<INSTRUCTION> &node);
    void removeNodeMaintainConnections(NetworkNode<INSTRUCTION> &node);
    size_t getNodeCount() { return network->GetNodes(); }
    std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> getGraphInputLayers();
    Graph getInstructionGraph()
    {
        auto instruction_graph = this->clone();
        auto all_nodes         = instruction_graph.getNodes();
        for (auto node : all_nodes)
        {
            if (node.GetDat().type != graph::OPERATION)
            {
                instruction_graph.removeNodeMaintainConnections(node);
            }
        }
        return instruction_graph;
    }
    Graph getDataGraph()
    {
        auto instruction_graph = this->clone();
        auto all_nodes         = instruction_graph.getNodes();
        for (auto node : all_nodes)
        {
            if (node.GetDat().type == graph::OPERATION)
            {
                instruction_graph.removeNodeMaintainConnections(node);
            }
        }
        return instruction_graph;
    }

    //Graph manipulation functions
    void renderGraphToPNGDot(const std::string &filename, LABEL_OPTION label) const;
    void writeDotFile(const std::string &filename, LABEL_OPTION label) const;
    Graph getNodeDependencyGraph(int start_node_id, bool trace_ancestors, bool trace_dependents) const;

private:
    Network<INSTRUCTION> cloneGraph(const Network<INSTRUCTION> &input) const;
    void getOutputNodesInPlace(Network<INSTRUCTION> &graph_output_nodes);
    Network<INSTRUCTION> getOutputNodesInternal(const Network<INSTRUCTION> &graph) const;
    void getInputNodesInPlace(Network<INSTRUCTION> &graph);

    void reverseEdgeDirections(Network<INSTRUCTION> &graph);

    Network<INSTRUCTION> GetBfsTree(const Network<INSTRUCTION> &graph, int start_node_id, bool in_direction, bool out_direction) const;

    TIntStrH getDataNodeNames(Network<INSTRUCTION> graph) const;
    TIntStrH getInstructionResults(Network<INSTRUCTION> graph) const;

    std::map<std::string, std::vector<int>> node_ID_Map;
    Network<INSTRUCTION> network;
};

template <typename INSTRUCTION>
Graph<INSTRUCTION> Graph<INSTRUCTION>::createGraph(std::vector<INSTRUCTION *> instructions)
{
    Graph<INSTRUCTION> graph;
    graph.network = TNodeEDatNet<Node<INSTRUCTION>, Edge>::New();

    int node_id = 0;
    for (const auto &instruction : instructions)
    {
        int operation_ID = 0;
        Node<INSTRUCTION> test(instruction->Name() + "_" + std::to_string(node_id), node_id, OPERATION, instruction);
        graph.network->AddNode(node_id, test);
        operation_ID                           = node_id;
        graph.node_ID_Map[instruction->Name()] = std::vector<int>({ node_id });
        node_id++;

        auto op_node = graph.network->GetNDat(operation_ID);
        std::ostringstream oss;
        oss << instruction->Name() << "(";
        for (int x = 0; x < instruction->numInputOperands(); x++)
        {
            auto retrievedID = graph.node_ID_Map.find(instruction->getInputOperand(x).location());
            int input_ID     = 0;
            if (retrievedID == graph.node_ID_Map.end())
            {
                Node<INSTRUCTION> input(instruction->getInputOperand(x).location(), node_id,
                                        instruction->getInputOperand(x).immediate() ? IMMEDIATE : REGISTER_ADDRESS);
                graph.network->AddNode(node_id, input);
                input_ID                                                      = node_id;
                graph.node_ID_Map[instruction->getInputOperand(x).location()] = std::vector<int>({ input_ID });
                node_id++;
            }
            else
            {
                input_ID = retrievedID->second.back();
            }

            graph.network->AddEdge(input_ID, operation_ID);

            auto node = graph.network->GetNDat(input_ID);
            oss << node.output_string;
            if (x < instruction->numInputOperands() - 1)
            {
                oss << ",";
            }
        }
        oss << ")";
        op_node.output_string = oss.str();
        for (int x = 0; x < instruction->numOutputOperands(); x++)
        {
            auto retrievedID = graph.node_ID_Map.find(instruction->getOutputOperand(x).location());
            int output_ID    = 0;
            if (retrievedID == graph.node_ID_Map.end())
            {
                Node<INSTRUCTION> input(instruction->getOutputOperand(x).location(), node_id, REGISTER_ADDRESS);
                graph.network->AddNode(node_id, input);
                output_ID                                                      = node_id;
                graph.node_ID_Map[instruction->getOutputOperand(x).location()] = std::vector<int>({ output_ID });
                node_id++;
            }
            else
            {
                Node<INSTRUCTION> input(instruction->getOutputOperand(x).location(), node_id, REGISTER_ADDRESS);
                graph.network->AddNode(node_id, input);
                output_ID = node_id;
                retrievedID->second.push_back(node_id);
                //node_ID_Map[instruction->getOutputOperand(x).location()]=std::vector<int>({output_ID});
                node_id++;
            }

            graph.network->AddEdge(operation_ID, output_ID);
        }
    }

    TIntStrH outputs;
    return graph;
}

template <typename INSTRUCTION>
NetworkNode<INSTRUCTION> Graph<INSTRUCTION>::getNode(int node_id)
{
    try
    {
        for (auto node = network->BegNI(); node < network->EndNI(); node++)
        {
            if (node.GetId() == node_id)
                return node;
        }
        throw std::runtime_error("Requested Node ID does not exist");
    }
    catch (...)
    {
        throw;
    }
}

template <typename INSTRUCTION>
std::vector<NetworkNode<INSTRUCTION>> Graph<INSTRUCTION>::getNodes() const
{
    std::vector<NetworkNode<INSTRUCTION>> nodes;
    for (auto node = network->BegNI(); node < network->EndNI(); node++)
        nodes.push_back(node);

    return nodes;
}

template <typename INSTRUCTION>
std::vector<NetworkNode<INSTRUCTION>> Graph<INSTRUCTION>::getOutputNodes() const
{
    std::vector<NetworkNode<INSTRUCTION>> nodes;
    for (auto node = network->BegNI(); node < network->EndNI(); node++)
    {
        if (node.GetOutDeg() == 0)
        {
            nodes.push_back(node);
        }
    }

    return nodes;
}

template <typename INSTRUCTION>
std::vector<NetworkNode<INSTRUCTION>> Graph<INSTRUCTION>::getInputNodes(bool include_registers, bool include_immediates, bool include_operations) const
{
    std::vector<NetworkNode<INSTRUCTION>> nodes;
    for (auto node = network->BegNI(); node < network->EndNI(); node++)
    {
        if (node.GetInDeg() == 0 && ((node.GetDat().type == IMMEDIATE && include_immediates == true) || (node.GetDat().type == REGISTER_ADDRESS && include_registers == true) || (node.GetDat().type == OPERATION && include_operations == true)))
        {
            nodes.push_back(node);
        }
    }

    return nodes;
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::removeNode(NetworkNode<INSTRUCTION> &node)
{
    network->DelNode(node.GetId());
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::removeNodeMaintainConnections(NetworkNode<INSTRUCTION> &node)
{
    std::vector<int> prev_nodes;
    std::vector<int> after_nodes;

    for (int e = 0; e < node.GetInDeg(); e++)
    {
        const int prev = node.GetInNId(e);
        prev_nodes.push_back(prev);
    }

    for (int e = 0; e < node.GetOutDeg(); e++)
    {
        const int after = node.GetOutNId(e);
        after_nodes.push_back(after);
    }

    network->DelNode(node.GetId());

    for (auto pnode : prev_nodes)
    {
        for (auto anode : after_nodes)
        {
            network->AddEdge(pnode, anode);
        }
    }
    return;
}

template <typename INSTRUCTION>
std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> Graph<INSTRUCTION>::getGraphInputLayers()
{
    std::vector<std::vector<graph::NetworkNode<pisa::PISAInstruction>>> input_layers;
    auto instruction_graph_consumable = this->clone();
    //Layer peel
    while (instruction_graph_consumable.getNodeCount() > 0)
    {
        auto inputs = instruction_graph_consumable.getInputNodes();
        //        //input_layers.push_back(inputs);
        std::vector<graph::NetworkNode<pisa::PISAInstruction>> layer;
        for (auto &node : inputs)
        {

            layer.push_back(this->getNode(node.GetId()));
            //            //std::cout << *node.GetDat().instruction << std::endl;
            instruction_graph_consumable.removeNode(node);
            //            //std::cout << *node.GetDat().instruction << std::endl;
        }
        input_layers.push_back(layer);
    }
    return input_layers;
}

template <typename INSTRUCTION>
Network<INSTRUCTION> Graph<INSTRUCTION>::cloneGraph(const Network<INSTRUCTION> &input) const
{
    Network<INSTRUCTION> output_graph = Network<INSTRUCTION>::New();
    for (auto node = input->BegNI(); node != input->EndNI(); node++)
    {
        output_graph->AddNode(node);
    }
    for (auto edge = input->BegEI(); edge != input->EndEI(); edge++)
    {
        output_graph->AddEdge(edge);
    }
    return output_graph;
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::getOutputNodesInPlace(Network<INSTRUCTION> &graph_output_nodes)
{
    std::vector<int> non_zero_deg_out_nodes;
    for (auto node = graph_output_nodes->BegNI(); node != graph_output_nodes->EndNI(); node++)
    {
        if (node.GetOutDeg() > 0)
        {
            non_zero_deg_out_nodes.push_back(node.GetId());
        }
    }
    for (const auto &node : non_zero_deg_out_nodes)
        graph_output_nodes->DelNode(node);

    return;
}

template <typename INSTRUCTION>
Network<INSTRUCTION> Graph<INSTRUCTION>::getOutputNodesInternal(const Network<INSTRUCTION> &graph) const
{
    auto graph_output_nodes = cloneGraph(graph);
    getOutputNodesInPlace(graph_output_nodes);
    return graph_output_nodes;
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::getInputNodesInPlace(Network<INSTRUCTION> &graph)
{
    throw std::logic_error("getInputNodesInPlace not implemented.");
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::renderGraphToPNGDot(const std::string &filename, LABEL_OPTION label) const
{
    TIntStrH name;
    switch (label)
    {
    case LABEL_OPTION::NAME:
        name = getDataNodeNames(network);
        break;
    case LABEL_OPTION::OUT_STRING:
        name = getInstructionResults(network);
        break;
    default:
        throw std::logic_error("Unknown label");
    }

    TSnap::DrawGViz<Network<INSTRUCTION>>(network, gvlDot, filename.c_str(), "", name);
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::writeDotFile(const std::string &filename, LABEL_OPTION label) const
{
    TIntStrH name;
    switch (label)
    {
    case LABEL_OPTION::NAME:
        name = getDataNodeNames(network);
        break;
    case LABEL_OPTION::OUT_STRING:
        name = getInstructionResults(network);
        break;
    default:
        throw std::logic_error("Unknown label");
    }

    TSnap::SaveGViz<Network<INSTRUCTION>>(network, filename.c_str(), "", name);
}

template <typename INSTRUCTION>
Graph<INSTRUCTION> Graph<INSTRUCTION>::getNodeDependencyGraph(int start_node_id, bool trace_ancestors, bool trace_dependents) const
{
    Graph dependency_graph;
    dependency_graph.network = GetBfsTree(network, start_node_id, trace_ancestors, trace_dependents);
    return dependency_graph;
}

template <typename INSTRUCTION>
void Graph<INSTRUCTION>::reverseEdgeDirections(Network<INSTRUCTION> &graph)
{
    throw std::logic_error("reverseEdgeDirections not implemented.");
}

template <typename INSTRUCTION>
Network<INSTRUCTION> Graph<INSTRUCTION>::GetBfsTree(const Network<INSTRUCTION> &graph, int start_node_id, bool in_direction, bool out_direction) const
{
    TBreathFS<Network<INSTRUCTION>> BFS(graph);
    BFS.DoBfs(start_node_id, out_direction, in_direction, -1, TInt::Mx);
    Network<INSTRUCTION> tree = Network<INSTRUCTION>::New();
    BFS.NIdDistH.SortByDat();

    for (int i = 0; i < BFS.NIdDistH.Len(); i++)
    {
        const int NId  = BFS.NIdDistH.GetKey(i);
        const int Dist = BFS.NIdDistH[i];
        auto NI        = graph->GetNI(NId);
        if (!tree->IsNode(NId))
        {
            auto dataNode = graph->GetNI(NId);
            tree->AddNode(dataNode);
        }
    }

    for (int i = 0; i < BFS.NIdDistH.Len(); i++)
    {
        const int NId  = BFS.NIdDistH.GetKey(i);
        const int Dist = BFS.NIdDistH[i];
        auto NI        = graph->GetNI(NId);

        if (in_direction)
        {
            for (int e = 0; e < NI.GetInDeg(); e++)
            {
                const int Prev = NI.GetInNId(e);
                //  std::cout << "prev: " << Prev;
                //  std::cout << "    NId: " << NI.GetId() << std::endl;
                if (tree->IsNode(Prev) /*&& BFS.NIdDistH.GetDat(Prev)==Dist-1*/)
                {
                    tree->AddEdge(Prev, NId);
                }
            }
        }

        if (out_direction)
        {
            for (int e = 0; e < NI.GetOutDeg(); e++)
            {
                const int Prev = NI.GetOutNId(e);
                if (tree->IsNode(Prev) /*&& BFS.NIdDistH.GetDat(Prev)==Dist-1*/)
                {
                    tree->AddEdge(Prev, NId);
                }
            }
        }
    }

    return tree;
}

template <typename INSTRUCTION>
TIntStrH Graph<INSTRUCTION>::getDataNodeNames(Network<INSTRUCTION> graph) const
{
    TIntStrH name;
    for (auto node = graph->BegNI(); node != graph->EndNI(); node++)
    {
        name.AddDat(node.GetId()) = TStr(node.GetDat().label.c_str());
        std::string color         = "white";
        if (node.GetInDeg() == 0)
        {
            color = "skyblue3";
        }
        if (node.GetOutDeg() == 0)
        {
            color = "seagreen1";
        }

        std::string output_color_and_label = std::string(node.GetDat().label + '"' + ", style=filled, fillcolor=" + '"' + color);
        name.AddDat(node.GetId(), output_color_and_label.c_str());
    }
    return name;
}

template <typename INSTRUCTION>
TIntStrH Graph<INSTRUCTION>::getInstructionResults(Network<INSTRUCTION> graph) const
{
    TIntStrH name;
    for (auto node = graph->BegNI(); node != graph->EndNI(); node++)
    {
        std::ostringstream label_stream;
        label_stream << node.GetDat().label << "= ";

        auto *instruction = node.GetDat().instruction;
        if (instruction != nullptr)
        {
            //label_stream << instruction->outLabel();
        }
        const std::string label   = label_stream.str();
        name.AddDat(node.GetId()) = TStr(label.c_str());
    }
    return name;
}

/**
 * @brief printGraphInformation Prints out some high level summary information for an HE graph.
 * @param graph
 */
template <typename INSTRUCTION>
void printGraphInformation(Graph<INSTRUCTION> &graph, const std::string &desc)
{
    try
    {
        std::cout << desc << std::endl;
        graph.printGraphInfo();
        auto inputs  = graph.getInputNodes();
        auto outputs = graph.getOutputNodes();
        std::cout << "inputs:" << inputs.size() << '\n'
                  << with_delimiter(inputs, " , ") << '\n'
                  << "outputs:" << outputs.size() << '\n'
                  << with_delimiter(outputs, " , ") << std::endl;
    }
    catch (...)
    {
        throw;
    }
}
} // namespace graph
