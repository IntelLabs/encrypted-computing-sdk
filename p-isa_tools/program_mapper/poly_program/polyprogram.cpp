// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "polyprogram.h"
#include <stdexcept>

std::string toString(SCHEME scheme, bool lowercase)
{
    switch (scheme)
    {
    case SCHEME::BGV:
        if (!lowercase)
            return "BGV";
        else
            return "bgv";
    case SCHEME::CKKS:
        if (!lowercase)
            return "CKKS";
        else
            return "ckks";
    case SCHEME::BFV:
        if (!lowercase)
            return "BFV";
        else
            return "bfv";
    default:
        throw std::runtime_error("Error converting enum scheme to string");
    }
}

namespace pisa::poly {
const std::string &PolyOperation::Name() const
{
    return params.at("operation_name").first;
}

void PolyOperation::setOperationName(const std::string &newOperation_name)
{
    params["operation_name"] = std::pair(newOperation_name, ValueType::STRING);
}

int PolyOperation::getCipherDegree() const
{
    return input_locations.front().num_of_polynomials;
}

void PolyOperation::setCipherDegree(int newCipher_degree)
{
    params["cipher_degree"] = std::pair(std::to_string(newCipher_degree), ValueType::UINT32);
}

int PolyOperation::getRnsTerms() const
{
    return this->input_locations.front().num_of_rns_terms;
}

void PolyOperation::setRnsTerms(int newRns_terms)
{
    params["rns_terms"] = std::pair(std::to_string(newRns_terms), ValueType::UINT32);
}

int PolyProgram::getPolyModulusDegree() const
{
    return m_N;
}

void PolyProgram::setPolyModulusDegree(int newPoly_modulus_degree)
{
    m_N = newPoly_modulus_degree;
}

int PolyOperation::getGaloisElt() const
{
    try
    {
        return std::stoi(params.at("galois_elt").first);
    }
    catch (...)
    {
        return 0;
    }
}

void PolyOperation::setGaloisElt(int newGalois_elt)
{
    params["galois_elt"] = std::pair(std::to_string(newGalois_elt), ValueType::UINT32);
}

int PolyProgram::getAlpha() const
{
    return alpha;
}
void PolyProgram::setAlpha(int newAlpha)
{
    alpha = newAlpha;
}

const std::vector<std::shared_ptr<PolyOperation>> &PolyProgram::operations() const
{
    return m_operations;
}

const std::vector<PolyOperation *> PolyProgram::operationsRaw() const
{
    std::vector<PolyOperation *> operations;
    for (auto i : m_operations)
    {
        operations.push_back(i.get());
    }
    return operations;
}

void PolyProgram::addOperation(std::shared_ptr<PolyOperation> operation)
{
    operation->setParentProgram(std::make_shared<PolyProgram>(*this));
    m_operations.push_back(operation);
}

void PolyProgram::setOperations(const std::vector<std::shared_ptr<PolyOperation>> &newOperations)
{
    m_operations = newOperations;
}
int PolyProgram::getDNum() const
{
    return dnum;
}
void PolyProgram::setDNum(int newDNum)
{
    dnum = newDNum;
}
int PolyProgram::getQSize() const
{
    return q_size;
}
void PolyProgram::setQSize(int newQ_size)
{
    q_size = newQ_size;
}

int PolyProgram::getKeyRns() const
{
    return key_rns;
}

void PolyProgram::setKeyRns(int newKey_rns)
{
    key_rns = newKey_rns;
}

uint32_t PolyOperation::getFactor() const
{
    try
    {
        return std::stoul(params.at("factor").first);
    }
    catch (...)
    {
        return 0;
    }
}

void PolyOperation::setFactor(uint32_t newFactor)
{
    params["factor"] = std::pair(std::to_string(newFactor), ValueType::UINT32);
}

SCHEME PolyProgram::scheme() const
{
    return m_scheme;
}

void PolyProgram::setScheme(SCHEME newScheme)
{
    m_scheme = newScheme;
}

void PolyOperation::addInput(std::string arg, int poly_num, int rns_num)
{

    input_locations.push_back(Polynomial(arg, rns_num, poly_num));
}

void PolyOperation::addOutput(std::string arg, int poly_num, int rns_num)
{
    output_locations.push_back(Polynomial(arg, rns_num, poly_num));
}

const OperationDesc &PolyOperation::description() const
{
    return m_description;
}

void PolyOperation::setDescription(const OperationDesc &newDescription)
{
    m_description = newDescription;
}
#ifdef ENABLE_DATA_FORMATS
void PolyOperation::setComponents(const heracles::fhe_trace::Instruction &instr_pb)
{
    for (const auto &src : instr_pb.args().dests())
        addOutput(src.symbol_name(), src.num_rns(), src.order());
    for (const auto &src : instr_pb.args().srcs())
        addInput(src.symbol_name(), src.num_rns(), src.order());
    setRnsTerms(instr_pb.args().srcs(0).num_rns());
    setCipherDegree(instr_pb.args().srcs(0).order());
    for (const auto &[k, v] : instr_pb.args().params())
    {
        if (k == "galois_elt")
            setGaloisElt(stoi(v.value()));
        if (k == "factor")
            setFactor(stoi(v.value()));
        if (k == "operand")
            // For muli operations, the operand is the immediate scalar value
            // Store it as a parameter that will be used when generating the kernel
            setParam({ k, { v.value(), ValueType::DOUBLE } });
    }
}
heracles::fhe_trace::Instruction *PolyOperation::getProtobuffFHETraceInstruction()
{
    heracles::fhe_trace::Instruction *instruction = new heracles::fhe_trace::Instruction();

    instruction->set_op(this->Name());
    for (auto &output : this->output_locations)
    {
        auto dest = instruction->mutable_args()->add_dests();
        dest->set_symbol_name(output.register_name);
        dest->set_order(output.num_of_polynomials);
        dest->set_num_rns(output.num_of_rns_terms);
    }
    for (auto &input : this->input_locations)
    {
        auto src = instruction->mutable_args()->add_srcs();
        src->set_symbol_name(input.register_name);
        src->set_order(input.num_of_polynomials);
        src->set_num_rns(input.num_of_rns_terms);
    }

    // Parse through description and process any special arguments
    auto desc = this->description();
    //TODO: additional arguments not currently supported.
    for (auto param : desc.params)
    {
        if (param == GALOIS_ELT)
        {
            *((*instruction->mutable_args()->mutable_params())["galois_elt"].mutable_value()) = std::to_string(this->galois_elt);
        }
        if (param == FACTOR)
        {
            *((*instruction->mutable_args()->mutable_params())["factor"].mutable_value()) = std::to_string(this->factor);
        }
    }

    return instruction;
}
#endif

const std::pair<std::string, ValueType> PolyOperation::getParam(std::string key) const
{
    return params.at(key);
}

const std::pair<std::string, ValueType> PolyOperation::getParam(int component_index) const
{
    try
    {
        auto key = param_index_lookup.at(component_index);
        return params.at(key);
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during" << __FUNCTION__ << ", err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << " in file " << __FILE__ << std::endl;
        throw;
    }
}

const std::string PolyOperation::getParamKey(int component_index) const
{
    try
    {
        return param_index_lookup.at(component_index);
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during" << __FUNCTION__ << ", err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << " in file " << __FILE__ << std::endl;
        throw;
    }
}

void PolyOperation::setParam(std::pair<std::string, std::pair<std::string, ValueType>> param)
{
    int contains = params.count(param.first);

    params[param.first] = param.second;
    if (contains == 0)
    {
        param_index_lookup[param_index_lookup.size()] = param.first;
    }
}

std::map<std::string, std::pair<std::string, ValueType>> &PolyOperation::getParams()
{
    return params;
}

void PolyOperation::setParams(const std::map<std::string, std::pair<std::string, ValueType>> &newParams)
{
    params = newParams;
}

const std::vector<Polynomial> &PolyOperation::getOutputLocations() const
{
    return output_locations;
}

const std::vector<Polynomial> &PolyOperation::getInputLocations() const
{
    return input_locations;
}

std::shared_ptr<PolyProgram> PolyOperation::parentProgram() const
{
    return m_parent_program;
}

void PolyOperation::setParentProgram(std::shared_ptr<PolyProgram> newParent_program)
{
    m_parent_program = newParent_program;
}

} // namespace pisa::poly

#ifdef ENABLE_DATA_FORMATS
heracles::common::Scheme toFHETrace(SCHEME scheme)
{
    try
    {
        if (scheme == SCHEME::BGV)
        {
            return heracles::common::SCHEME_BGV;
        }
        else if (scheme == SCHEME::BFV)
        {
            return heracles::common::SCHEME_BFV;
        }
        else if (scheme == SCHEME::CKKS)
        {
            return heracles::common::SCHEME_CKKS;
        }
        else
            throw std::runtime_error("unknown scheme conversion request");
    }
    catch (...)
    {
        throw std::runtime_error("Error encountered during toFHETrace");
    }
}

SCHEME toPolyProgram(heracles::common::Scheme scheme)
{
    try
    {
        if (scheme == heracles::common::SCHEME_BGV)
        {
            return SCHEME::BGV;
        }
        else if (scheme == heracles::common::SCHEME_BFV)
        {
            return SCHEME::BFV;
        }
        else if (scheme == heracles::common::SCHEME_CKKS)
        {
            return SCHEME::CKKS;
        }
        else
            throw std::runtime_error("unknown scheme conversion request");
    }
    catch (...)
    {
        throw std::runtime_error("Error encountered during toHEProgram");
    }
}
#endif

SCHEME fromString(std::string scheme)
{
    try
    {
        if (scheme == "bgv" || scheme == "BGV")
        {
            return SCHEME::BGV;
        }
        else if (scheme == "bfv" || scheme == "BFV")
        {
            return SCHEME::BFV;
        }
        else if (scheme == "ckks" || scheme == "CKKS")
        {
            return SCHEME::CKKS;
        }
        else
            throw std::runtime_error("unknown scheme conversion request");
    }
    catch (...)
    {
        throw std::runtime_error("Error encountered during toHEProgram");
    }
}
