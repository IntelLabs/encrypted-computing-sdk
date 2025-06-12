// Copyright (C) 2023 Intel Corporation

#include "pisa_test_generator.h"
#include "functional_modeler/data_handlers/json_data_handler.h"
#include "functional_modeler/pisa_runtime/pisaprogramruntime.h"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <string>

PisaTestGenerator::PisaTestGenerator()
{
}

void PisaTestGenerator::populateCalculatedOutputResults(std::vector<pisa::PISAInstruction *> instructions, json &input)
{
    PISAProgramRuntime<uint32> evaluator;
    //Setup data
    auto json_data                    = JSONDataHandler<uint32>(input);
    std::vector<uint32> modulus_chain = json_data.getModulusChain();
    auto trace_ntt_twiddle_factors    = json_data.getNTTTwiddleFactors();
    auto trace_intt_twiddle_factors   = json_data.getINTTTwiddleFactors();

    auto trace_inputs     = json_data.getAllInputs();
    auto trace_immediates = json_data.getAllimmediatesAsVec(1);

    evaluator.setModulusChain(modulus_chain);
    auto chain = evaluator.getModulusChain();

    evaluator.setNTTTwiddleFactors(trace_ntt_twiddle_factors);
    evaluator.setINTTTwiddleFactors(trace_intt_twiddle_factors);

    evaluator.setParamMemoryToMultiRegisterDeviceMemory(trace_inputs);
    evaluator.setImmediatesToMultiRegisterDeviceMemory(trace_immediates);

    evaluator.executeProgram(instructions);

    auto trace_outputs = json_data.getAllOutputs();
    auto outputs       = input["output"].items();

    for (const auto &output : outputs)
    {
        auto result = evaluator.getParamMemoryFromMultiRegisterDeviceMemory(output.key());

        for (int x = 0; x < output.value().size(); x++)
        {
            input["output"][output.key()][x] = result.second[x];
        }
    }
    return;
}

json PisaTestGenerator::generateJSONForGraph(graph::Graph<pisa::PISAInstruction> p_isa_graph, pisa::testgenerator::InputGenerationMode gen_mode, unsigned int random_seed)
{
    json new_json;
    auto inputs     = p_isa_graph.getInputNodes(true, false, false);
    auto immediates = p_isa_graph.getInputNodes(false, true, false);
    auto outputs    = p_isa_graph.getOutputNodes();

    for (auto &input : inputs)
    {
        const std::string key = input.GetDat().label;

        for (int x = 0; x < block_size; x++)
        {
            if (gen_mode == pisa::testgenerator::InputGenerationMode::SINGLE_ONE)
            {
                new_json["input"][key][x] = (x == 0) ? 1 : 0;
            }
            else if (gen_mode == pisa::testgenerator::InputGenerationMode::ALL_ONES)
            {
                new_json["input"][key][x] = 1;
            }
            else if (gen_mode == pisa::testgenerator::InputGenerationMode::ASCENDING_FROM_ZERO)
            {
                new_json["input"][key][x] = x;
            }
            else if (gen_mode == pisa::testgenerator::InputGenerationMode::ONE_RANDOM)
            {
                new_json["input"][key][x] = (x == 0) ? rand() % modulus_value : 0;
            }
            else if (gen_mode == pisa::testgenerator::InputGenerationMode::ALL_RANDOM)
            {
                new_json["input"][key][x] = rand_r(&random_seed) % modulus_value;
            }
        }
    }

    for (auto &output : outputs)
    {
        const std::string key = output.GetDat().label;

        for (int x = 0; x < block_size; x++)
        {
            new_json["output"][key][x] = 0;
        }
    }

    addMetaDataInformation(new_json);

    for (auto &immediate : immediates)
    {
        const std::string key = immediate.GetDat().label;

        int register_size = 1;

        for (int x = 0; x < register_size; x++)
        {
            new_json["metadata"]["immediate"][key] = 1;
        }
    }

    convertPolyRnsChunkToPolyRns(new_json);

    return new_json;
}

int PisaTestGenerator::findMaxRNSNumber(json &input_json)
{
    int max_rns = 0;

    auto inputs = input_json.find("input");

    for (auto input : inputs->items())
    {
        auto label              = input.key();
        int block_divider       = label.find_last_of('_');
        auto block_removed      = label.substr(0, block_divider);
        int rns_divider         = block_removed.find_last_of('_');
        std::string rns_val_str = block_removed.substr(rns_divider + 1);
        int rns_val             = std::atoi(rns_val_str.c_str());
        max_rns                 = std::max(rns_val, max_rns);
    }

    return max_rns + 1;
}

void PisaTestGenerator::addMetaDataInformation(json &input_json, int rns_num)
{
    input_json["metadata"]["scheme"] = "custom";
    for (int x = 0; x < rns_num; x++)
    {
        input_json["metadata"]["RNS_modulus"][x] = modulus_value;
    }

    for (int x = 0; x < rns_num; x++)
    {
        for (int y = 0; y < block_size; y++)
        {
            input_json["metadata"]["twiddle"]["ntt"][x][y]  = 1;
            input_json["metadata"]["twiddle"]["intt"][x][y] = 1;
        }
    }

    //Add the default immediate values
    input_json["metadata"]["immediate"]["iN"]                = 1;
    input_json["metadata"]["immediate"]["iN_0"]              = 1;
    input_json["metadata"]["immediate"]["iN_1"]              = 1;
    input_json["metadata"]["immediate"]["iN_2"]              = 1;
    input_json["metadata"]["immediate"]["R2_0"]              = 1;
    input_json["metadata"]["immediate"]["R2_1"]              = 1;
    input_json["metadata"]["immediate"]["R2_2"]              = 1;
    input_json["metadata"]["immediate"]["one"]               = 1;
    input_json["metadata"]["immediate"]["pinv_q_0"]          = 1;
    input_json["metadata"]["immediate"]["pinv_q_1"]          = 1;
    input_json["metadata"]["immediate"]["t_inverse_mod_p_0"] = 1;
    input_json["metadata"]["immediate"]["t_0"]               = 1;
    input_json["metadata"]["immediate"]["t_1"]               = 1;
    input_json["metadata"]["immediate"]["t_2"]               = 1;

    return;
}

void PisaTestGenerator::addMetaDataInformation(json &input_json)
{
    auto rns_num = findMaxRNSNumber(input_json);
    addMetaDataInformation(input_json, rns_num);
}

void PisaTestGenerator::convertPolyRnsChunkToPolyRns(json &input_json)
{
    convertPolyRnsChunkToPolyRnsHelper(input_json["input"]);
    convertPolyRnsChunkToPolyRnsHelper(input_json["output"]);
}

void PisaTestGenerator::convertPolyRnsChunkToPolyRnsHelper(json &input_json)
{
    std::map<std::string, std::vector<std::pair<std::string, int>>> collections;
    for (auto input : input_json.items())
    {
        auto label         = input.key();
        int block_divider  = label.find_last_of('_');
        auto block_removed = label.substr(0, block_divider);
        int block_number   = std::stoi(label.substr(block_divider + 1));

        // This creates my ordered vectors
        //std::cout << "Adding to collection: " << block_removed << " , " << label << " , " << block_number << std::endl;
        collections[block_removed].push_back(std::pair<std::string, int>(label, block_number));
    }
    for (auto &collection : collections)
    {
        //Sort vector based on block number
        std::sort(collection.second.begin(), collection.second.end(), [](const std::pair<std::string, int> &a, const std::pair<std::string, int> &b) { return a.second < b.second; });

        for (auto chunk : collection.second)
        {
            for (auto block_value : input_json[chunk.first].items())
            {
                //std::cout << "Block V"
                input_json[collection.first][input_json[collection.first].size()] = block_value.value();
            };
        }
        //Remove block item from json once data is transferred
        int items_to_remove = collection.second.size();
        for (int x = 0; x < items_to_remove; x++)
        {
            auto chunk_val = input_json.find(collection.second[x].first);
            input_json.erase(chunk_val);
        }
    }
}

void PisaTestGenerator::writeJSON(json input_json, std::string file_name)
{
    auto serialized_json = input_json.dump(1, ' ', true);
    std::ofstream output;
    output.open(file_name);
    output << serialized_json;
}
