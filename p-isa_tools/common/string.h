
// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <algorithm>
#include <string>

inline std::string whiteSpaceRemoved(const std::string &str)
{
    auto str_copy = str;
    auto trimmed  = std::remove(str_copy.begin(), str_copy.end(), ' ');
    str_copy.erase(trimmed, str_copy.end());
    return str_copy;
}
