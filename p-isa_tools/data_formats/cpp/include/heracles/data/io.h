// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <sstream>
#include <string>
#include <unordered_map>
#include "heracles/proto/data.pb.h"

namespace heracles::data
{
using hdf_manifest = std::unordered_map<std::string, std::unordered_map<std::string, std::string>>;

hdf_manifest parse_manifest(const std::string &filename);
void generate_manifest(const std::string &filename, const hdf_manifest &manifest);

bool store_data_trace(
    const std::string &filename, const heracles::data::FHEContext &context_pb,
    const heracles::data::TestVector &testvector_pb);
std::pair<heracles::data::FHEContext, heracles::data::TestVector> load_data_trace(const std::string &filename);

void store_hec_context(
    hdf_manifest *manifest_out, const std::string &filename, const heracles::data::FHEContext &context_pb);
void store_testvector(
    hdf_manifest *manifest_out, const std::string &filename, const heracles::data::TestVector &testvector_pb);
heracles::data::FHEContext load_hec_context(const std::string &filename);
heracles::data::TestVector load_testvector(const std::string &filename);

void load_hec_context_from_manifest(heracles::data::FHEContext *context_pb, const hdf_manifest &manifest);
void load_testvector_from_manifest(heracles::data::TestVector *testvector_pb, const hdf_manifest &manifest);

//==================================
// For debugging
//==================================
bool store_hec_context_json(const std::string &filename, const heracles::data::FHEContext &context);
bool store_testvector_json(const std::string &filename, const heracles::data::TestVector &test_vector);
} // namespace heracles::data
