// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "pisa_instruction_tests/add_instruction_test.h"
#include "pisa_instruction_tests/copy_instruction_test.h"
#include "pisa_instruction_tests/intt_instruction_test.h"
#include "pisa_instruction_tests/mac_instruction_test.h"
#include "pisa_instruction_tests/maci_instruction_test.h"
#include "pisa_instruction_tests/mul_instruction_test.h"
#include "pisa_instruction_tests/muli_instruction_test.h"
#include "pisa_instruction_tests/ntt_instruction_test.h"
#include "pisa_instruction_tests/pisa_instruction_test.h"
#include "pisa_instruction_tests/random_instr_stream_instruction_test.h"
#include "pisa_instruction_tests/sub_instruction_test.h"
#include <map>

static std::map<std::string, PisaInstructionTest *> pisa_instruction_tests = { { addInstructionTest::operationName(), new addInstructionTest() },
                                                                               { mulInstructionTest::operationName(), new mulInstructionTest() },
                                                                               { muliInstructionTest::operationName(), new muliInstructionTest() },
                                                                               { macInstructionTest::operationName(), new macInstructionTest() },
                                                                               { maciInstructionTest::operationName(), new maciInstructionTest() },
                                                                               { nttInstructionTest::operationName(), new nttInstructionTest() },
                                                                               { inttInstructionTest::operationName(), new inttInstructionTest() },
                                                                               { subInstructionTest::operationName(), new subInstructionTest() },
                                                                               { copyInstructionTest::operationName(), new copyInstructionTest() },
                                                                               { RandomStreamInstructionTest::operationName(), new RandomStreamInstructionTest() } };
