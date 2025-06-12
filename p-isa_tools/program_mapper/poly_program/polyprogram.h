// Copyright (C) 2023 Intel Corporation

#pragma once

#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <iostream>

#include "operations/core.h"
#include "polynomial.h"

#ifdef ENABLE_DATA_FORMATS
#include <heracles/heracles_proto.h>
#endif

enum class SCHEME
{
    BGV,
    CKKS,
    BFV
};

std::string toString(SCHEME scheme, bool lowercase = false);
SCHEME fromString(std::string scheme);
#ifdef ENABLE_DATA_FORMATS
heracles::common::Scheme toFHETrace(SCHEME scheme);
SCHEME toPolyProgram(heracles::common::Scheme scheme);
std::string getOpName(const heracles::fhe_trace::Instruction &instruction_pb);
#endif

namespace pisa::poly {

class PolyOperation;

/**
 * @brief The PolyProgram class holds a collection of Polynomial Operations and context information in which to perform those operations.
 */
class PolyProgram
{
public:
    PolyProgram() {}
    static std::shared_ptr<PolyProgram> create() { return std::make_shared<PolyProgram>(); }
    SCHEME scheme() const;
    void setScheme(SCHEME newScheme);
    int getPolyModulusDegree() const;
    void setPolyModulusDegree(int newPoly_modulus_degree);
    int getKeyRns() const;
    void setKeyRns(int newKey_rns);
    int getDNum() const;
    void setDNum(int newDNum);
    int getQSize() const;
    void setQSize(int newQ_size);
    int getAlpha() const;
    void setAlpha(int newAlpha);
    const std::vector<std::shared_ptr<PolyOperation>> &operations() const;
    const std::vector<PolyOperation *> operationsRaw() const;
    void addOperation(std::shared_ptr<PolyOperation> operation);
    void setOperations(const std::vector<std::shared_ptr<PolyOperation>> &newOperations);

private:
    int m_N         = 14;
    int key_rns     = 4;
    int alpha       = 0;
    int dnum        = 0;
    int q_size      = 1;
    SCHEME m_scheme = SCHEME::BGV;

    std::vector<std::shared_ptr<PolyOperation>> m_operations;
};

static PolyProgram default_global_poly_program;

//ValueType enum for POLY_PROGRAM
enum ValueType
{
    UINT32 = 0,
    UINT64 = 1,
    INT32  = 2,
    INT64  = 3,
    FLOAT  = 4,
    DOUBLE = 5,
    STRING = 6
};

struct Operand
{
    Operand(const std::string &location) :
        location_(location) {}
    std::string location() const { return location_; }

    const std::string location_;
    /* Added temporarily as a compatibility fix */
    bool immediate() const { return false; }
};

/**
 * @brief The PolyOperation class represents a polynomial operation involving 1 or more input polynomial objects.
 */
class PolyOperation
{
public:
    PolyOperation() {}
    PolyOperation(const PolyOperationDesc &desc)
    {
        m_description  = desc.desc;
        operation_name = desc.name;
    }
    template <class Iterator>
    PolyOperation(const PolyOperationDesc &desc, Iterator start, Iterator end, std::shared_ptr<pisa::poly::PolyProgram> parent)
    {
        m_description  = desc.desc;
        operation_name = desc.name;
        setParentProgram(parent);
        setOperationName(desc.name);

        std::tuple<std::string, int, int> decomposed;
        int index = 0;
        for (auto iter = start; iter != end; ++iter)
        {
            PARAM_TYPE operation = m_description.params[index];
            std::string value    = *iter;
            switch (operation)
            {
            case OP_NAME:
                if (!desc.force_desc_op_name)
                    setOperationName(value);
                break;
            case INPUT_ARGUMENT:
                decomposed = Polynomial::decomposePolyStringForm(value);
                addInput(std::get<0>(decomposed), std::get<1>(decomposed), std::get<2>(decomposed));
                break;
            case OUTPUT_ARGUMENT:
                decomposed = Polynomial::decomposePolyStringForm(value);
                addOutput(std::get<0>(decomposed), std::get<1>(decomposed), std::get<2>(decomposed));
                break;
            case INPUT_OUTPUT_ARGUMENT:
                decomposed = Polynomial::decomposePolyStringForm(value);
                addInput(std::get<0>(decomposed), std::get<1>(decomposed), std::get<2>(decomposed));
                addOutput(std::get<0>(decomposed), std::get<1>(decomposed), std::get<2>(decomposed));
                break;
            case POLYMOD_DEG_LOG2:
                m_parent_program->setPolyModulusDegree(stoi(value));
                break;
            case CIPHER_DEGREE:
                setCipherDegree(stoi(value));
                break;
            case RNS_TERM:
                setRnsTerms(stoi(value));
                break;
            case FHE_SCHEME:
                m_parent_program->setScheme(fromString(value));
                break;
            case PARAM:
                throw std::runtime_error("Params not current supported by poly_program initializer list");
                break;
            case GALOIS_ELT:
                setGaloisElt(stoi(value));
                break;
            case FACTOR:
                setFactor(stoi(value));
                break;
            case KEY_RNS:
                m_parent_program->setKeyRns(stoi(value));
                break;
            case ALPHA:
                m_parent_program->setAlpha(stoi(value));
                break;
            case QSIZE:
                m_parent_program->setQSize(stoi(value));
                break;
            case DNUM:
                m_parent_program->setDNum(stoi(value));
                break;
            }
            index++;
        }
    }

    static std::string baseName() { return std::string("Default OP"); }

    virtual std::shared_ptr<PolyOperation> create() { return std::make_shared<PolyOperation>(); }
    static std::shared_ptr<PolyOperation> create(PolyOperationDesc desc) { return std::make_shared<PolyOperation>(desc); }

    static std::shared_ptr<PolyOperation> create(PolyOperationDesc desc, std::initializer_list<std::string> args, std::shared_ptr<pisa::poly::PolyProgram> parent)
    {
        if (args.size() > desc.desc.params.size())
        {
            throw std::runtime_error("Number of arguments does not match requested polynomial operation description");
        }
        else if ((args.size() < desc.desc.params.size()))
        {
            std::cerr << "WARNING: " << desc.name << " specifies " << desc.desc.params.size() << " but only " << args.size() << " were provided";
        }

        return std::make_shared<PolyOperation>(desc, args.begin(), args.end(), parent);
    }
    static std::shared_ptr<PolyOperation> create(PolyOperationDesc desc, std::vector<std::string> args, std::shared_ptr<pisa::poly::PolyProgram> parent)
    {
        if (args.size() > desc.desc.params.size())
        {
            throw std::runtime_error("Number of arguments does not match requested polynomial operation description");
        }
        else if ((args.size() < desc.desc.params.size()))
        {
            std::cerr << "WARNING: " << desc.name << " specifies " << desc.desc.params.size() << " but only " << args.size() << " were provided";
        }
        return std::make_shared<PolyOperation>(desc, args.begin(), args.end(), parent);
    }

    std::string outLabel() { return ""; }

    void addInput(std::string arg, int poly_num, int rns_num);
    void addOutput(std::string arg, int poly_num, int rns_num);
    int numInputOperands() const { return input_locations.size(); }
    int numOutputOperands() const { return output_locations.size(); }
    Polynomial getInputOperand(int x) const { return input_locations[x]; }
    Polynomial getOutputOperand(int x) const { return output_locations[x]; }

    const OperationDesc &description() const;
    void setDescription(const OperationDesc &newDescription);
    const std::string &Name() const;
    void setOperationName(const std::string &newOperation_name);
    int getCipherDegree() const;
    void setCipherDegree(int newCipher_degree);
    int getRnsTerms() const;
    void setRnsTerms(int newRns_terms);
    int getGaloisElt() const;
    void setGaloisElt(int newGalois_elt);
    uint32_t getFactor() const;
    void setFactor(uint32_t newFactor);

#ifdef ENABLE_DATA_FORMATS
    void setComponents(const heracles::fhe_trace::Instruction &instr_pb);
    heracles::fhe_trace::Instruction *getProtobuffFHETraceInstruction();
#endif

    // Param System
    const std::pair<std::string, ValueType> getParam(std::string key) const;
    const std::pair<std::string, ValueType> getParam(int component_index) const;
    const std::string getParamKey(int component_index) const;
    void setParam(std::pair<std::string, std::pair<std::string, ValueType>> param);

    // PolyProgram level operations if present

    std::shared_ptr<PolyProgram> parentProgram() const;
    void setParentProgram(std::shared_ptr<PolyProgram> newParent_program);

    const std::vector<Polynomial> &getInputLocations() const;
    const std::vector<Polynomial> &getOutputLocations() const;

protected:
    std::map<std::string, std::pair<std::string, ValueType>> &getParams();
    void setParams(const std::map<std::string, std::pair<std::string, ValueType>> &newParams);

    int rns_terms;
    int cipher_degree;
    int galois_elt;
    uint32_t factor;

    std::string operation_name;
    std::vector<Polynomial> input_locations;
    std::vector<Polynomial> output_locations;
    std::map<std::string, std::pair<std::string, ValueType>> params;
    std::map<int, std::string> param_index_lookup;
    OperationDesc m_description;
    std::shared_ptr<PolyProgram> m_parent_program = std::make_shared<PolyProgram>(default_global_poly_program);
};

} // namespace pisa::poly

class ProgramTrace
{
public:
    ProgramTrace() = default;
};
