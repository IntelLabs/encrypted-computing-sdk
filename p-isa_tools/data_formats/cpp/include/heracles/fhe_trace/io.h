// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <iostream>
#include <string>
#include "heracles/proto/fhe_trace.pb.h"

namespace heracles::fhe_trace
{
/*
        Serialize and store a HE op trace.
    */
bool store_trace(const std::string &filename, const heracles::fhe_trace::Trace &trace);

/*
        Load and deserialize a HEC context.
    */
heracles::fhe_trace::Trace load_trace(const std::string &filename);

/*
        Serialize and store a HE op trace in JSON format.
    */
bool store_json_trace(const std::string &filename, const heracles::fhe_trace::Trace &trace);

/*
        Load and deserialize a HE op trace from JSON format.
    */
heracles::fhe_trace::Trace load_json_trace(const std::string &filename);

} // namespace heracles::fhe_trace
