// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/fhe_trace/io.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <google/protobuf/util/json_util.h>
#include <iostream>

namespace heracles::fhe_trace
{
bool store_trace(const std::string &filename, const heracles::fhe_trace::Trace &trace)
{
    std::ofstream pb_ofile(filename, std::ios::out | std::ios::binary);
    return trace.SerializeToOstream(&pb_ofile);
}

heracles::fhe_trace::Trace load_trace(const std::string &filename)
{
    std::ifstream pb_ifile(filename, std::ios::binary);
    heracles::fhe_trace::Trace trace;
    if (!trace.ParseFromIstream(&pb_ifile))
        throw std::runtime_error("Cannot read from file : " + filename);
    return trace;
}

bool store_json_trace(const std::string &filename, const heracles::fhe_trace::Trace &trace)
{
    std::string str;
    google::protobuf::util::JsonPrintOptions options;
    options.add_whitespace = true;
    options.always_print_primitive_fields = true;
    auto status = google::protobuf::util::MessageToJsonString(trace, &str, options);
    if (!status.ok())
        return false;
    std::ofstream json_ofile(filename, std::ios::out);
    json_ofile << str;
    return true;
}

heracles::fhe_trace::Trace load_json_trace(const std::string &filename)
{
    std::ifstream json_ifile(filename);
    if (!json_ifile.is_open())
    {
        throw std::runtime_error("Cannot open file: " + filename);
    }

    std::string json_str((std::istreambuf_iterator<char>(json_ifile)), std::istreambuf_iterator<char>());

    heracles::fhe_trace::Trace trace;
    auto status = google::protobuf::util::JsonStringToMessage(json_str, &trace);
    if (!status.ok())
    {
        throw std::runtime_error("Cannot parse JSON from file: " + filename);
    }

    return trace;
}
} // namespace heracles::fhe_trace
