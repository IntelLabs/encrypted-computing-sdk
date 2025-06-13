// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>

#ifdef ENABLE_DATA_FORMATS
#include "google/protobuf/util/json_util.h"
#endif
#include <common/string.h>

#include "program_mapper/poly_program/poly_operation_library.h"
#include "program_trace_helper.h"

#ifdef ENABLE_DATA_FORMATS
#include <heracles/heracles_data_formats.h>
#endif

#ifdef ENABLE_DATA_FORMATS
std::shared_ptr<pisa::poly::PolyProgram> PolynomialProgramHelper::parse(const heracles::fhe_trace::Trace &trace_pb, bool verbose)
{
    try
    {
        if (verbose)
            heracles::util::fhe_trace::print_trace(trace_pb);
        auto program = pisa::poly::PolyProgram::create();

        std::string scheme = heracles::common::Scheme_descriptor()
                                 ->FindValueByNumber(trace_pb.scheme())
                                 ->options()
                                 .GetExtension(heracles::common::string_name);

        program->setScheme(toPolyProgram(trace_pb.scheme()));
        program->setPolyModulusDegree(trace_pb.n());
        program->setKeyRns(trace_pb.key_rns_num());
        program->setAlpha(trace_pb.alpha());
        program->setQSize(trace_pb.q_size());
        program->setDNum(trace_pb.dnum());

        for (const auto &inst_pb : trace_pb.instructions())
        {
            std::string op = inst_pb.op();
            if (op.substr(0, 3) == "bk_")
                continue;

            auto instr = pisa::poly::library::createPolyOperation(op);
            instr->setOperationName(op);
            instr->setComponents(inst_pb);
            program->addOperation(instr);
        }
        return program;
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during ProgramTraceParser::Parse, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}
#endif

std::shared_ptr<pisa::poly::PolyProgram> PolynomialProgramHelper::parse(const std::string &filename_or_prefix, POLYNOMIAL_PROGRAM_FORMAT format, bool ignore_header)
{
    try
    {

        if (format == POLYNOMIAL_PROGRAM_FORMAT::CSV)
        {
            return parseCSV(filename_or_prefix, ignore_header);
        }
#ifdef ENABLE_DATA_FORMATS
        else if (format == POLYNOMIAL_PROGRAM_FORMAT::PROTOBUFF)
        {
            return parseProtoBuff(filename_or_prefix);
        }
#endif
        else
        {
            throw std::runtime_error("UNSUPPORTED TRACE FORMAT");
        }
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during parse, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}

std::shared_ptr<pisa::poly::PolyProgram> PolynomialProgramHelper::parseCSV(const std::string &filename, bool ignore_header)
{
    try
    {
        auto new_poly_program = pisa::poly::PolyProgram::create();

        std::ifstream file(filename);
        if (!file.is_open())
        {
            throw std::runtime_error("File not found: " + filename);
        }

        std::string current_line;
        if (ignore_header)
            std::getline(file, current_line);

        while (std::getline(file, current_line))
        {
            std::vector<std::string> components;
            std::stringstream current_line_ss(current_line);

            std::string component;
            while (std::getline(current_line_ss, component, ','))
            {
                components.push_back(trim(component));
            }
            new_poly_program->addOperation(parseInstruction(components, new_poly_program));
        }
        return new_poly_program;
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during parse, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}

#ifdef ENABLE_DATA_FORMATS
std::shared_ptr<pisa::poly::PolyProgram> PolynomialProgramHelper::parseProtoBuff(const std::string &filename, bool verbose)
{
    try
    {
        heracles::fhe_trace::Trace trace_pb = heracles::fhe_trace::load_trace(filename);
        return parse(trace_pb);
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during parse, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}
#endif

void PolynomialProgramHelper::writeTraceToCSV(const std::shared_ptr<pisa::poly::PolyProgram> trace, std::string file_name)
{
    try
    {
        std::vector<std::string> instructions;
        std::ofstream file(file_name);
        if (!file.is_open())
        {
            throw std::runtime_error("File not found: " + file_name);
        }

        std::string header = "scheme,poly_modulus_degree,rns_terms,cipher_degree,instruction,arg0,arg1,arg2,arg3,arg4,arg5,arg6,arg7,arg8,arg9";
        file << header << "\n";
        for (auto &HE_op : trace->operations())
        {

            auto instruction_components = writeToASCIIComponents(HE_op);

            std::string he_op_string;
            //Write string
            for (auto component : instruction_components)
            {
                he_op_string += component + ",";
            }
            he_op_string.pop_back();

            file << he_op_string << "\n";
        }
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during writeTraceToCSV, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}

#ifdef ENABLE_DATA_FORMATS
void PolynomialProgramHelper::writeTraceToProtoBuff(const std::shared_ptr<pisa::poly::PolyProgram> trace, std::string file_name)
{
    try
    {
        // Create sample trace
        heracles::fhe_trace::Trace protobuff_trace;
        protobuff_trace.set_n(trace->getPolyModulusDegree());
        // - context
        auto HE_scheme = trace->scheme();
        protobuff_trace.set_scheme(toFHETrace(HE_scheme));
        auto key_rns = trace->getKeyRns();
        protobuff_trace.set_key_rns_num(key_rns);

        for (auto &instr : trace->operations())
        {
            auto proto_instr = instr->getProtobuffFHETraceInstruction();
            protobuff_trace.add_instructions()->CopyFrom(*proto_instr);
        }

        std::cout << "debug string: " << protobuff_trace.DebugString() << std::endl;
        std::string json;
        auto rc = google::protobuf::util::MessageToJsonString(protobuff_trace, &json);
        std::cout << "json: " << json << std::endl;

        //        // accessing enums as default strings and as our own version ..
        auto scheme = protobuff_trace.scheme();
        std::cout << "scheme: as-num=" << scheme
                  << " / as-default-string=" << heracles::common::Scheme_descriptor()->FindValueByNumber(scheme)->name()
                  << " / as-friendly-string="
                  << heracles::common::Scheme_descriptor()->value(scheme)->options().GetExtension(
                         heracles::common::string_name)
                  << std::endl;

        // serialize it to file
        if (!heracles::fhe_trace::store_trace(file_name, protobuff_trace))
        {
            std::cerr << "Could not serialize" << std::endl;
            exit(1);
        }
    }
    catch (const std::runtime_error &err)
    {
        std::cout << "Runtime error during writeTraceToCSV, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cout << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}
#endif

std::shared_ptr<pisa::poly::PolyOperation> PolynomialProgramHelper::parseInstruction(const std::vector<std::string> &components, std::shared_ptr<pisa::poly::PolyProgram> program)
{
    try
    {
        std::string operation = components[OP_CODE_LOCATION];
        auto trimmed          = std::remove(operation.begin(), operation.end(), ' ');
        operation.erase(trimmed, operation.end());

        auto new_instruction = pisa::poly::library::createPolyOperation(operation, components, program);

        return new_instruction;
    }
    catch (const std::out_of_range &err)
    {
        throw std::runtime_error("No Instruction Desc found for operation in InstructionMap map. Operation: " + components[OP_CODE_LOCATION]);
    }
    catch (...)
    {
        std::cout << "Invalid instruction detected during parsing.";
        throw;
    }
}

std::vector<std::string> PolynomialProgramHelper::writeToASCIIComponents(const std::shared_ptr<pisa::poly::PolyOperation> operation)
{
    try
    {
        std::vector<std::string> components;
        auto op_desc = operation->description();

        int count = 0;
        for (int component_index = 0; component_index < op_desc.params.size(); component_index++)
        {
            std::string op_value;
            extractComponent(operation, op_value, component_index);
            components.push_back(op_value);
        }
        return components;
    }
    catch (...)
    {
        std::cout << "Error during parswriteToASCIIComponentsing.";
        throw;
    }
}

#ifdef ENABLE_DATA_FORMATS
std::shared_ptr<pisa::poly::PolyOperation> PolynomialProgramHelper::parseInstruction(const heracles::fhe_trace::Instruction &instruction_pb)
{
    // get op name
    std::string op = instruction_pb.op();
    try
    {
        auto instr = pisa::poly::library::createPolyOperation(op);

        instr->setOperationName(op);
        instr->setComponents(instruction_pb);

        return instr;
    }
    catch (const std::out_of_range &err)
    {
        throw std::runtime_error("No Instruction Desc found for operation in InstructionMap map. Operation: " + op);
    }
    catch (...)
    {
        std::cout << "Invalid instruction detected during parsing.";
        throw;
    }
}
#endif

void PolynomialProgramHelper::parseComponent(const std::string &component, PARAM_TYPE type, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    switch (type)
    {
    case CIPHER_DEGREE:
        parse_CIPHER_DEGREE(component, instr);
        break;
    case OP_NAME:
        parse_OP_NAME(component, instr);
        break;
    case INPUT_ARGUMENT:
        parse_INPUT_ARGUMENT(component, instr);
        break;
    case OUTPUT_ARGUMENT:
        parse_OUTPUT_ARGUMENT(component, instr);
        break;
    case INPUT_OUTPUT_ARGUMENT:
        parse_INPUT_OUTPUT_ARGUMENT(component, instr);
        break;
    case POLYMOD_DEG_LOG2:
        parse_POLYMOD_DEG_LOG2(component, instr);
        break;
    case RNS_TERM:
        parse_RNS_TERM(component, instr);
        break;
    case FHE_SCHEME:
        parse_FHE_SCHEME(component, instr);
        break;
    case GALOIS_ELT:
        parse_GALOIS_ELT(component, instr);
        break;
    case FACTOR:
        parse_FACTOR(component, instr);
        break;
    case KEY_RNS:
        parse_KEY_RNS(component, instr);
        break;
    case PARAM:
    case ALPHA:
    case DNUM:
    case QSIZE:
        throw std::runtime_error("Not implemented");
    default:
        throw std::runtime_error("Unhandled component during parsing");
    }
}

void PolynomialProgramHelper::extractComponent(const std::shared_ptr<pisa::poly::PolyOperation> instr, std::string &component, int component_index)
{
    auto type = instr->description().params[component_index];

    switch (type)
    {
    case CIPHER_DEGREE:
        extract_CIPHER_DEGREE(component, instr, component_index);
        break;
    case OP_NAME:
        extract_OP_NAME(component, instr, component_index);
        break;
    case INPUT_ARGUMENT:
        extract_INPUT_ARGUMENT(component, instr, component_index);
        break;
    case OUTPUT_ARGUMENT:
        extract_OUTPUT_ARGUMENT(component, instr, component_index);
        break;
    case INPUT_OUTPUT_ARGUMENT:
        extract_INPUT_OUTPUT_ARGUMENT(component, instr, component_index);
        break;
    case POLYMOD_DEG_LOG2:
        extract_POLYMOD_DEG_LOG2(component, instr, component_index);
        break;
    case RNS_TERM:
        extract_RNS_TERM(component, instr, component_index);
        break;
    case FHE_SCHEME:
        extract_FHE_SCHEME(component, instr, component_index);
        break;
    case GALOIS_ELT:
        extract_GALOIS_ELT(component, instr, component_index);
        break;
    case FACTOR:
        extract_FACTOR(component, instr, component_index);
        break;
    case KEY_RNS:
        extract_KEY_RNS(component, instr, component_index);
        break;
    case PARAM:
    case ALPHA:
    case DNUM:
    case QSIZE:
        throw std::runtime_error("Not implemented");
    default:
        throw std::runtime_error("Unhandled component during parsing");
    }
}

#ifdef ENABLE_DATA_FORMATS
heracles::fhe_trace::Instruction *PolynomialProgramHelper::getProtobuffInstruction(std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    return instr->getProtobuffFHETraceInstruction();
}
#endif

void PolynomialProgramHelper::parse_OP_NAME(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setOperationName(whiteSpaceRemoved(component));
}

void PolynomialProgramHelper::parse_CIPHER_DEGREE(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setCipherDegree(stoi(component));
}

void PolynomialProgramHelper::parse_INPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    //    instr->addInput(component);
}

void PolynomialProgramHelper::parse_OUTPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    //    instr->addOutput(component);
}

void PolynomialProgramHelper::parse_INPUT_OUTPUT_ARGUMENT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    //   instr->addInput(component);
    //   instr->addOutput(component);
}

void PolynomialProgramHelper::parse_POLYMOD_DEG_LOG2(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->parentProgram()->setPolyModulusDegree(std::stoi(component));
}

void PolynomialProgramHelper::parse_RNS_TERM(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setRnsTerms(std::stoi(component));
}

void PolynomialProgramHelper::parse_FHE_SCHEME(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->parentProgram()->setScheme(fromString(component));
}

void PolynomialProgramHelper::parse_GALOIS_ELT(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setGaloisElt(std::stoi(component));
}

void PolynomialProgramHelper::parse_FACTOR(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setFactor(std::stoi(component));
}

void PolynomialProgramHelper::parse_KEY_RNS(const std::string &component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->parentProgram()->setKeyRns(stoi(component));
}

void PolynomialProgramHelper::parse_PARAM(const std::pair<std::string, std::pair<std::string, pisa::poly::ValueType>> component, std::shared_ptr<pisa::poly::PolyOperation> instr)
{
    instr->setParam(component);
}

void PolynomialProgramHelper::extract_OP_NAME(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = instr->Name();
}

void PolynomialProgramHelper::extract_CIPHER_DEGREE(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->getCipherDegree());
}

void PolynomialProgramHelper::extract_INPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    int desired_input_index = 0;
    auto desc               = instr->description();
    for (int x = 0; x < component_index; x++)
    {
        if (desc.params[x] == PARAM_TYPE::INPUT_ARGUMENT || desc.params[x] == PARAM_TYPE::INPUT_OUTPUT_ARGUMENT)
        {
            desired_input_index++;
        }
    }
    component = instr->getInputOperand(desired_input_index).register_name;
}

void PolynomialProgramHelper::extract_OUTPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    int desired_output_index = 0;
    auto desc                = instr->description();
    for (int x = 0; x < component_index; x++)
    {
        if (desc.params[x] == PARAM_TYPE::OUTPUT_ARGUMENT || desc.params[x] == PARAM_TYPE::INPUT_OUTPUT_ARGUMENT)
        {
            desired_output_index++;
        }
    }
    component = instr->getOutputOperand(desired_output_index).register_name;
}

void PolynomialProgramHelper::extract_INPUT_OUTPUT_ARGUMENT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    int desired_output_index = 0;
    auto desc                = instr->description();
    for (int x = 0; x < component_index; x++)
    {
        if (desc.params[x] == PARAM_TYPE::OUTPUT_ARGUMENT || desc.params[x] == PARAM_TYPE::INPUT_OUTPUT_ARGUMENT)
        {
            desired_output_index++;
        }
    }
    component = instr->getOutputOperand(desired_output_index).register_name;
}

void PolynomialProgramHelper::extract_POLYMOD_DEG_LOG2(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->parentProgram()->getPolyModulusDegree());
}

void PolynomialProgramHelper::extract_RNS_TERM(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->getRnsTerms());
}

void PolynomialProgramHelper::extract_FHE_SCHEME(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = toString(instr->parentProgram()->scheme());
}

void PolynomialProgramHelper::extract_GALOIS_ELT(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->getGaloisElt());
}

void PolynomialProgramHelper::extract_FACTOR(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->getFactor());
}

void PolynomialProgramHelper::extract_KEY_RNS(std::string &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    component = std::to_string(instr->parentProgram()->getKeyRns());
}

void PolynomialProgramHelper::extract_PARAM(std::pair<std::string, std::pair<std::string, pisa::poly::ValueType>> &component, const std::shared_ptr<pisa::poly::PolyOperation> instr, int component_index)
{
    int desired_param_index = 0;
    auto desc               = instr->description();
    for (int x = 0; x < component_index; x++)
    {
        if (desc.params[x] == PARAM_TYPE::PARAM)
        {
            desired_param_index++;
        }
    }

    auto key         = instr->getParamKey(component_index);
    component.first  = key;
    component.second = instr->getParam(key);
}
