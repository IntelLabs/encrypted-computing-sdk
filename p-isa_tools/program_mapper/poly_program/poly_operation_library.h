// Copyright (C) 2023 Intel Corporation

#pragma once

#include "polyprogram.h"

namespace pisa::poly::library {
/** Map used to specify the collection of kernels */
static std::map<std::string, PolyOperationDesc> core_operation_library = {
    { "add", library::core::Add },
    { "add_plain", library::core::Add },
    { "sub", library::core::Sub },
    { "mul", library::core::Mul },
    { "mul_plain", library::core::Mul },
    { "square", library::core::Square },
    { "ntt", library::core::Ntt },
    { "intt", library::core::Intt },
    { "relin", library::core::Relin },
    { "mod_switch", library::core::ModSwitch },
    { "rescale", library::core::Rescale },
    { "rotate", library::core::Rotate },
};

static std::map<std::string, PolyOperationDesc> extended_operation_set;
static std::map<std::string, PolyOperationDesc> active_polynomial_operation_library;

static void activatePolynomialLibrary()
{
    active_polynomial_operation_library.merge(core_operation_library);

    for (auto item : extended_operation_set)
    {
        active_polynomial_operation_library[item.first] = item.second;
    }
}

static bool library_ready = false;

static PolyOperationDesc getPolyOperationDesc(std::string operation)
{
    if (library_ready == false)
    {
        activatePolynomialLibrary();
    }

    if (active_polynomial_operation_library.count(operation) == 0)
    {
        throw std::runtime_error("Operation: " + operation + " requested during parseInstruction but no instruction description found");
    }
    auto new_instance = active_polynomial_operation_library[operation];
    return new_instance;
}

static std::shared_ptr<pisa::poly::PolyOperation> createPolyOperation(std::string operation)
{
    auto new_instance    = getPolyOperationDesc(operation);
    auto new_instruction = pisa::poly::PolyOperation::create(new_instance);
    return new_instruction;
}

static std::shared_ptr<pisa::poly::PolyOperation> createPolyOperation(std::string operation, std::initializer_list<std::string> args, std::shared_ptr<pisa::poly::PolyProgram> parent)
{
    auto new_instance    = getPolyOperationDesc(operation);
    auto new_instruction = pisa::poly::PolyOperation::create(new_instance, args, parent);
    return new_instruction;
}
static std::shared_ptr<pisa::poly::PolyOperation> createPolyOperation(std::string operation, std::initializer_list<std::string> args)
{
    return createPolyOperation(operation, args, std::make_shared<pisa::poly::PolyProgram>(pisa::poly::default_global_poly_program));
}

static std::shared_ptr<pisa::poly::PolyOperation> createPolyOperation(std::string operation, std::vector<std::string> args, std::shared_ptr<pisa::poly::PolyProgram> parent)
{
    auto new_instance    = getPolyOperationDesc(operation);
    auto new_instruction = pisa::poly::PolyOperation::create(new_instance, args, parent);
    return new_instruction;
}
static std::shared_ptr<pisa::poly::PolyOperation> createPolyOperation(std::string operation, std::vector<std::string> args)
{
    return createPolyOperation(operation, args, std::make_shared<pisa::poly::PolyProgram>(pisa::poly::default_global_poly_program));
}

} // namespace pisa::poly::library
