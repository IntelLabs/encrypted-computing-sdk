// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

#include <nlohmann/json.hpp>
using json = nlohmann::json;
template <typename T>
using TwiddleMap = std::unordered_map<std::string, std::vector<std::vector<T>>>;

/**
 * @brief The JSONDataHandler class provides an interface for accessing inputs/outputs and meta data stored in a JSON file. Supports operation on hec formatted and raw traces.
 */
template <typename T>
class JSONDataHandler
{
public:
    JSONDataHandler() = default;
    JSONDataHandler(const std::string &json_filename, bool hec_format_data = true);
    JSONDataHandler(const json &input_json);

    std::vector<T> getModulusChain() const;
    std::vector<T> getInputVector(const std::string &name) const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllInputs() const;
    void addInputs(std::vector<std::pair<std::string, std::vector<T>>> inputs);
    void writeJSON() const;
    void setAllInputsToOne();
    std::vector<std::pair<std::string, std::vector<T>>> getAllOutputs() const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllIntermediatess() const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllimmediatesAsVec(int width) const;
    std::vector<std::vector<T>> getNTTTwiddleFactors() const;
    TwiddleMap<T> getINTTTwiddleFactors() const;

    json m_input_json;
    bool v0_mode;
};

template <typename T>
JSONDataHandler<T>::JSONDataHandler(const std::string &json_filename, bool hec_format_data)
{
    try
    {
        std::ifstream input_json_data(json_filename);
        m_input_json = json::parse(input_json_data);
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error while parsing in JSONDataHandler, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::ostringstream oss;
        oss << "Unknown exception caught in "
            << __func__
            << " in file "
            << __FILE__;
        throw std::runtime_error(oss.str());
    }
}

template <typename T>
JSONDataHandler<T>::JSONDataHandler(const json &input_json)
{
    m_input_json = input_json;
}

template <typename T>
std::vector<T> JSONDataHandler<T>::getModulusChain() const
{
    try
    {
        std::vector<T> values;
        auto modulus_chain = m_input_json.find("metadata")->find("RNS_modulus");
        if (!modulus_chain->empty())
        {
            for (const auto &s : modulus_chain->items())
            {
                values.push_back(s.value());
            }
        }

        return values;
    }
    catch (...)
    {
        throw std::runtime_error("No modulus chain found");
    }
}

template <typename T>
std::vector<T> JSONDataHandler<T>::getInputVector(const std::string &name) const
{
    try
    {
        std::vector<T> values;
        auto input = m_input_json.find("input")->find(name);
        if (!input->empty())
        {
            for (const auto &s : input->items())
            {
                std::cout << "Input:" << s.value() << std::endl;
                values.push_back(s.value());
            }
        }

        return values;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> JSONDataHandler<T>::getAllInputs() const
{
    try
    {
        std::vector<std::pair<std::string, std::vector<T>>> input_memory_vectors;
        auto inputs = m_input_json.find("input");
        if (!inputs->empty())
        {
            for (const auto &input : inputs->items())
            {
                std::string input_label = input.key();
                std::vector<T> values;
                for (const auto &s : input.value().items())
                {
                    values.push_back(s.value());
                }
                input_memory_vectors.emplace_back(input_label, values);
            }
        }

        return input_memory_vectors;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
void JSONDataHandler<T>::addInputs(std::vector<std::pair<std::string, std::vector<T>>> inputs)
{
    try
    {
        std::vector<std::pair<std::string, std::vector<T>>> input_memory_vectors;
        auto new_json   = json(nullptr);
        auto input_test = new_json.find("input");

        auto inputss = new_json.find("input");

        for (auto &input : inputs)
        {
            std::string key = input.first;

            int x = 0;
            for (auto val : input.second)
            {
                new_json["input"][key][x++] = val;
            }
        }

        auto serialized_json              = new_json.dump(1, ' ', true);
        const std::string output_filepath = "output_json_input_test.json";
        std::ofstream output(output_filepath);
        if (!output.is_open())
        {
            throw std::runtime_error("Could not open file '" + output_filepath + "' for writing.");
        }
        output << serialized_json;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": Failure while adding input");
    }
}

template <typename T>
void JSONDataHandler<T>::writeJSON() const
{
    auto serialized_json = m_input_json.dump(1, ' ', true);
    std::ofstream output;
    output.open("output_json.json");
    output << serialized_json;
}

template <typename T>
void JSONDataHandler<T>::setAllInputsToOne()
{
    try
    {
        auto inputs = m_input_json.find("input");
        if (!inputs->empty())
        {
            for (auto &input : inputs->items())
            {
                std::string input_label = input.key();
                std::vector<T> values;
                for (auto &s : input.value().items())
                {
                    auto &val   = s.value();
                    val.front() = 1;
                }
            }
        }
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> JSONDataHandler<T>::getAllIntermediatess() const
{
    try
    {
        std::vector<std::pair<std::string, std::vector<T>>> intermediate_memory_vectors;
        if (m_input_json.contains("intermediate"))
        {
            auto intermediates = m_input_json.find("intermediate");
            if (!intermediates->empty())
            {
                for (const auto &intermediate : intermediates->items())
                {
                    std::string intermediate_label = intermediate.key();
                    std::vector<T> values;
                    for (const auto &s : intermediate.value().items())
                    {
                        values.push_back(s.value());
                    }
                    intermediate_memory_vectors.emplace_back(intermediate_label, values);
                }
            }

            return intermediate_memory_vectors;
        }
        else
        {
            return std::vector<std::pair<std::string, std::vector<T>>>();
        }
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": Error when getting intermediates");
    }
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> JSONDataHandler<T>::getAllOutputs() const
{
    try
    {
        std::vector<std::pair<std::string, std::vector<T>>> output_memory_vectors;
        std::vector<T> values;
        auto outputs = m_input_json.find("output");
        if (!outputs->empty())
        {
            for (const auto &output : outputs->items())
            {
                std::cout << "Output:" << output.key() << std::endl;
                std::string input_label = output.key();
                std::vector<T> values;
                for (const auto &s : output.value().items())
                {
                    values.push_back(s.value());
                }
                output_memory_vectors.emplace_back(input_label, values);
            }
        }

        return output_memory_vectors;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> JSONDataHandler<T>::getAllimmediatesAsVec(int width) const
{
    try
    {
        std::vector<std::pair<std::string, std::vector<T>>> input_memory_vectors;
        if (!m_input_json.contains("metadata"))
        {
            return input_memory_vectors;
        }
        auto metadata = m_input_json["metadata"];
        auto inputs   = metadata.find("immediate");
        if (inputs != metadata.end() && !inputs->empty())
        {
            for (const auto &input : inputs->items())
            {
                std::string input_label = input.key();
                std::vector<T> values;
                for (int x = 0; x < width; x++)
                {
                    values.push_back(input.value());
                }
                input_memory_vectors.emplace_back(input_label, values);
            }
        }

        return input_memory_vectors;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
std::vector<std::vector<T>> JSONDataHandler<T>::getNTTTwiddleFactors() const
{
    try
    {
        std::vector<std::vector<T>> input_metadata_vectors;
        std::vector<T> values;
        auto inputs = m_input_json.find("metadata")->find("twiddle")->find("ntt");
        if (!inputs->empty())
        {
            for (const auto &input : inputs->items())
            {
                std::string input_label = input.key();
                std::vector<T> values;
                for (const auto &s : input.value().items())
                {
                    values.push_back(s.value());
                }
                input_metadata_vectors.push_back(std::move(values));
            }
        }

        return input_metadata_vectors;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}

template <typename T>
TwiddleMap<T> JSONDataHandler<T>::getINTTTwiddleFactors() const
{
    try
    {
        TwiddleMap<T> intt_tf;
        std::vector<T> values;
        auto inputs = m_input_json.find("metadata")->find("twiddle")->find("intt");
        if (!inputs->empty())
        {
            for (const auto &input : inputs->items())
            {
                std::string intt_name = input.key();
                std::vector<T> values;
                for (const auto &s : input.value().items())
                {
                    values.push_back(s.value());
                }
                // TODO: once INTT instruction is updated, change "default" to input_label
                //std::string input_label = intt_name == "default" ? "1" : intt_name;
                std::string input_label = "1";
                intt_tf[input_label].push_back(std::move(values));
            }
        }

        return intt_tf;
    }
    catch (...)
    {
        throw std::runtime_error(std::string(__func__) + ": No input found");
    }
}
