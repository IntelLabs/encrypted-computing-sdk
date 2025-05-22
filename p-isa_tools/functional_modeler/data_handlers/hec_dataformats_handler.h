// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <string>
#include <unordered_map>
#include <unordered_set>

#include <config.h>
#include <iostream>
#include <stdexcept>
#include <vector>

#if ENABLE_DATA_FORMATS
#include <heracles/heracles_data_formats.h>
#include <heracles/heracles_proto.h>

template <typename T>
using TwiddleMap     = std::unordered_map<std::string, std::vector<std::vector<T>>>;
using DataSymbolsSet = std::pair<std::unordered_set<std::string>, std::unordered_set<std::string>>;

/**
 * @brief The HecDataFormatsHandler class provides an interface for accessing inputs/outputs and meta data stored in a hec_dataformats data file
 */
template <typename T>
class HecDataFormatsHandler
{
public:
    HecDataFormatsHandler() = default;
    HecDataFormatsHandler(const std::string &polynomial_program_filename, const std::string &dataformats_data, bool hec_format = true);
    HecDataFormatsHandler(const heracles::data::FHEContext &context_pb, const heracles::data::TestVector &testvector_pb,
                          const heracles::fhe_trace::Trace &polynomial_program_pb);

    std::vector<T> getModulusChain() const;
    std::vector<T> getInputVector(const std::string &name) const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllInputs() const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllOutputs() const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllIntermediates() const;
    std::vector<std::string> getAllInputSyms() const;
    std::vector<std::string> getAllOutputSyms() const;
    std::vector<std::string> getAllIntermediateSyms() const;
    std::vector<std::pair<std::string, std::vector<T>>> getAllimmediatesAsVec(int width) const;
    std::vector<std::vector<T>> getNTTTwiddleFactors() const;
    TwiddleMap<T> getINTTTwiddleFactors() const;

    heracles::data::MetadataPolynomials m_metadataPolys;
    heracles::data::MetadataTwiddles m_metadataTwiddles;
    heracles::data::MetadataImmediates m_metadataImmediates;
    heracles::data::MetadataParams m_metadataParams;
    heracles::data::DataPolynomials m_polys;

    // additional parameters
    std::vector<T> m_RNSModulus;
    std::unordered_set<std::string> m_inputSymbols;
    std::unordered_set<std::string> m_outputSymbols;
    std::unordered_set<std::string> m_intermediateSymbols;

private:
    void parseProtobufTestVector(const heracles::data::FHEContext &context_pb,
                                 const heracles::data::TestVector &testvector_pb,
                                 const heracles::fhe_trace::Trace &polynomial_program_pb);
    void processDataSymbols(const DataSymbolsSet &allsymbols);
};

template <typename T>
void HecDataFormatsHandler<T>::parseProtobufTestVector(const heracles::data::FHEContext &context_pb, const heracles::data::TestVector &testvector_pb,
                                                       const heracles::fhe_trace::Trace &polynomial_program_pb)
{
    // extract from context
    heracles::data::extract_metadata_immediates(&m_metadataImmediates, context_pb);
    heracles::data::extract_metadata_twiddles(&m_metadataTwiddles, context_pb);
    heracles::data::extract_metadata_polys(&m_metadataPolys, context_pb);
    heracles::data::extract_polys(&m_polys, testvector_pb);
    heracles::data::extract_metadata_params(&m_metadataParams, context_pb);
    m_RNSModulus = std::vector<uint32_t>(context_pb.q_i().begin(), context_pb.q_i().end());
    // get data symbol designation (input, output, intermediate)
    processDataSymbols(heracles::util::fhe_trace::get_all_symbols(polynomial_program_pb));
}

template <typename T>
void HecDataFormatsHandler<T>::processDataSymbols(const DataSymbolsSet &allsymbols)
{
    for (const auto &[sym, rnspoly] : m_polys.data().sym_poly_map())
    {
        // TODO: this feature could be in utils (used everywhere)
        int size      = sym.find('_', 0);
        auto rootname = sym.substr(0, size);

        bool foundInInput  = allsymbols.first.find(rootname) != allsymbols.first.end();
        bool foundInOutput = allsymbols.second.find(rootname) != allsymbols.second.end();

        if (!foundInInput && !foundInOutput)
        {
            continue;
        }
        // found as both input and output
        if (foundInInput && foundInOutput)
        {
            m_intermediateSymbols.insert(sym);
        }
        // found only in input
        else if (foundInInput)
        {
            m_inputSymbols.insert(sym);
        }
        else // found only in output
        {
            m_outputSymbols.insert(sym);
        }
    }
}

template <typename T>
HecDataFormatsHandler<T>::HecDataFormatsHandler(const heracles::data::FHEContext &context_pb, const heracles::data::TestVector &testvector_pb,
                                                const heracles::fhe_trace::Trace &polynomial_program_pb)
{
    parseProtobufTestVector(context_pb, testvector_pb, polynomial_program_pb);
}

template <typename T>
HecDataFormatsHandler<T>::HecDataFormatsHandler(const std::string &polynomial_program_filename, const std::string &dataformats_data, bool hec_format)
{
    auto [context_pb, testvector_pb]    = heracles::data::load_data_trace(dataformats_data);
    heracles::fhe_trace::Trace trace_pb = heracles::fhe_trace::load_trace(polynomial_program_filename);

    parseProtobufTestVector(context_pb, testvector_pb, trace_pb);
}

template <typename T>
std::vector<T> HecDataFormatsHandler<T>::getModulusChain() const
{
    return m_RNSModulus;
}

template <typename T>
std::vector<T> HecDataFormatsHandler<T>::getInputVector(const std::string &name) const
{
    if (m_polys.data().sym_poly_map().find(name) != m_polys.data().sym_poly_map().end())
    {
        return std::vector<T>(m_polys.data().sym_poly_map().at(name).coeffs().begin(),
                              m_polys.data().sym_poly_map().at(name).coeffs().end());
    }

    if (m_metadataPolys.metadata().sym_poly_map().find(name) != m_metadataPolys.metadata().sym_poly_map().end())
    {
        return std::vector<T>(m_metadataPolys.metadata().sym_poly_map().at(name).coeffs().begin(),
                              m_metadataPolys.metadata().sym_poly_map().at(name).coeffs().end());
    }

    return {}; // Empty std::vector
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> HecDataFormatsHandler<T>::getAllInputs() const
{
    std::vector<std::pair<std::string, std::vector<T>>> input_memory_vectors;

    // all inputs and metapolys
    for (const std::string &sym : m_inputSymbols)
    {
        input_memory_vectors.emplace_back(sym,
                                          std::vector<T>(m_polys.data().sym_poly_map().at(sym).coeffs().begin(),
                                                         m_polys.data().sym_poly_map().at(sym).coeffs().end()));
    }
    for (const auto &[sym, rnspoly] : m_metadataPolys.metadata().sym_poly_map())
    {
        input_memory_vectors.emplace_back(sym,
                                          std::vector<T>(rnspoly.coeffs().begin(), rnspoly.coeffs().end()));
    }

    return input_memory_vectors;
}

template <typename T>
std::vector<std::string> HecDataFormatsHandler<T>::getAllInputSyms() const
{
    std::vector<std::string> input_syms(m_inputSymbols.begin(), m_inputSymbols.end());

    for (const auto &[sym, rnspoly] : m_metadataPolys.metadata().sym_poly_map())
    {
        input_syms.push_back(sym);
    }

    return input_syms;
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> HecDataFormatsHandler<T>::getAllIntermediates() const
{
    if (m_intermediateSymbols.empty())
    {
        return {};
    }

    std::vector<std::pair<std::string, std::vector<T>>> intermediate_memory_vectors;
    for (const auto &sym : m_intermediateSymbols)
    {
        intermediate_memory_vectors.emplace_back(sym,
                                                 std::vector<T>(m_polys.data().sym_poly_map().at(sym).coeffs().begin(),
                                                                m_polys.data().sym_poly_map().at(sym).coeffs().end()));
    }
    return intermediate_memory_vectors;
}
template <typename T>
std::vector<std::string> HecDataFormatsHandler<T>::getAllIntermediateSyms() const
{
    return std::vector<std::string>(m_intermediateSymbols.begin(), m_intermediateSymbols.end());
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> HecDataFormatsHandler<T>::getAllOutputs() const
{
    std::vector<std::pair<std::string, std::vector<T>>> output_memory_vectors;

    for (const auto &sym : m_outputSymbols)
    {
        output_memory_vectors.emplace_back(sym,
                                           std::vector<T>(m_polys.data().sym_poly_map().at(sym).coeffs().begin(),
                                                          m_polys.data().sym_poly_map().at(sym).coeffs().end()));
    }
    return output_memory_vectors;
}

template <typename T>
std::vector<std::string> HecDataFormatsHandler<T>::getAllOutputSyms() const
{
    return std::vector<std::string>(m_outputSymbols.begin(), m_outputSymbols.end());
}

template <typename T>
std::vector<std::pair<std::string, std::vector<T>>> HecDataFormatsHandler<T>::getAllimmediatesAsVec(int width) const
{
    std::vector<std::pair<std::string, std::vector<T>>> input_memory_vectors;
    if (width > 1)
        throw std::runtime_error("Width of protobuf immediates must be 1 !");
    for (const auto &[sym, value] : m_metadataImmediates.sym_immediate_map())
    {
        input_memory_vectors.emplace_back(sym, std::vector<T>{ value });
    }

    return input_memory_vectors;
}

template <typename T>
std::vector<std::vector<T>> HecDataFormatsHandler<T>::getNTTTwiddleFactors() const
{
    std::vector<std::vector<T>> input_metadata_vectors;
    auto ntt_1 = m_metadataTwiddles.twiddles_ntt().find("default");
    if (ntt_1 != m_metadataTwiddles.twiddles_ntt().end())
    {
        for (const auto &s : ntt_1->second.rns_polys())
        {
            input_metadata_vectors.push_back(std::vector<T>(s.coeffs().begin(), s.coeffs().end()));
        }
    }

    return input_metadata_vectors;
}

template <typename T>
TwiddleMap<T> HecDataFormatsHandler<T>::getINTTTwiddleFactors() const
{
    TwiddleMap<T> input_metadata_vectors;
    for (const auto &[intt_name, poly] : m_metadataTwiddles.twiddles_intt())
    {
        // convert "default" to "1" (default)
        std::string input_label = intt_name == "default" ? "1" : intt_name;
        std::vector<std::vector<T>> metadata_vector;
        for (const auto &rnspoly : poly.rns_polys())
        {
            metadata_vector.push_back(std::vector<T>(rnspoly.coeffs().begin(), rnspoly.coeffs().end()));
        }
        input_metadata_vectors[input_label] = metadata_vector;
    }

    return input_metadata_vectors;
}
#endif
