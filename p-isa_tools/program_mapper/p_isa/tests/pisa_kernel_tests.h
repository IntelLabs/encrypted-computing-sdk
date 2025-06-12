// Copyright (C) 2023 Intel Corporation

#pragma once

#include "pisa_kernel_tests/add.h"
#include "pisa_kernel_tests/add_corrected.h"
#include "program_mapper/poly_program/poly_operation_library.h"
//#include "pisa_kernel_tests/add_plain.h"
//#include "pisa_kernel_tests/base_operation.h"
//#include "pisa_kernel_tests/chained_adds.h"
//#include "pisa_kernel_tests/intt.h"
//#include "pisa_kernel_tests/mod_switch.h"
//#include "pisa_kernel_tests/mul.h"
//#include "pisa_kernel_tests/mul_plain.h"
//#include "pisa_kernel_tests/multiply_constant_inplace.h"
//#include "pisa_kernel_tests/ntt.h"
//#include "pisa_kernel_tests/relin.h"
//#include "pisa_kernel_tests/rescale.h"
//#include "pisa_kernel_tests/rotate.h"
//#include "pisa_kernel_tests/square.h"
//#include "pisa_kernel_tests/wide_add.h"
#include <map>

//#TODO These items are commented out for now as they will need to be updated to new programtrace format but
//the trace is still undergoing some additional improvements/reworks so to avoid lots of unnecessary code updates
//just a few test classes are enabled until full refactor done then all tests will be reworked to upgraded style.
static std::map<std::string, PisaKernelTest *> pisa_kernel_tests = {
    // { ChainedAdds::operationName(), new ChainedAdds() },
    { AddOperation::operationName(), new AddOperation() },
    { AddCorrected::operationName(), new AddCorrected() },
    // { AddPlain::operationName(), new AddPlain() },
    // { Intt::operationName(), new Intt() },
    // { ModSwitchOperation::operationName(), new ModSwitchOperation() },
    // { MulOperation::operationName(), new MulOperation() },
    // { MulPlainOperation::operationName(), new MulPlainOperation() },
    // { MultiplyConstantInplaceOperation::operationName(), new MultiplyConstantInplaceOperation() },
    // { NttOperation::operationName(), new NttOperation() },
    // { RelinOperation::operationName(), new RelinOperation() },
    // { RescaleOperation::operationName(), new RescaleOperation() },
    // { RotateOperation::operationName(), new RotateOperation() },
    // { SquareOperation::operationName(), new SquareOperation() },
    // { WideAdd::operationName(), new WideAdd() }
};
