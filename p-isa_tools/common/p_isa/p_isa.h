// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "p_isa_instructions.h"
#include <map>

namespace pisa {

///** InstructionMap provides a mapping from OP name to implementation of that instruction.
// *
// **/

static const std::map<std::string, PISAInstruction *> InstructionMap = {
    { instruction::Add::baseName, new instruction::Add() },
    { instruction::Sub::baseName, new instruction::Sub() },
    { instruction::Mul::baseName, new instruction::Mul() },
    { instruction::Mac::baseName, new instruction::Mac() },
    { instruction::Maci::baseName, new instruction::Maci() },
    { instruction::Intt::baseName, new instruction::Intt() },
    { instruction::Ntt::baseName, new instruction::Ntt() },
    { instruction::Muli::baseName, new instruction::Muli() },
    { instruction::Copy::baseName, new instruction::Copy() }
};

} // namespace pisa
