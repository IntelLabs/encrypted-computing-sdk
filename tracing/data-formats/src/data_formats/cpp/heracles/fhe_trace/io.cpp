// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/fhe_trace/io.h"
#include <cstdint>
#include <filesystem>
#include <fstream>
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
} // namespace heracles::fhe_trace
