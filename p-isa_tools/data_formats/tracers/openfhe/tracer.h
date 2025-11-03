// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#ifndef P_ISA_TOOLS_DATA_FORMATS_TRACERS_OPENFHE_TRACER_H_
#define P_ISA_TOOLS_DATA_FORMATS_TRACERS_OPENFHE_TRACER_H_

// Defines ENABLE_TRACER (via config_core.h) so needs to be outside the #ifdef ENABLE_TRACER_SUPPORT
#include "utils/tracing.h"

#ifdef ENABLE_TRACER

#ifdef WITH_OPENMP
#include <omp.h>
#endif
#include <algorithm>
#include <cassert>
#include <complex>
#include <fstream>
#include <iomanip>
#include <memory>
#include <mutex>
#include <sstream>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

#include "ciphertext-ser.h"
#include "cryptocontext-ser.h"
#include "key/key-ser.h"
#include "plaintext-ser.h"
#include "scheme/bfvrns/bfvrns-ser.h"
#include "scheme/bgvrns/bgvrns-ser.h"
#include "scheme/ckksrns/ckksrns-ser.h"
#include "utils/hashutil.h"

#include <heracles/data/io.h>
#include <heracles/heracles_data_formats.h>
#include <heracles/heracles_proto.h>

namespace lbcrypto {

// Note: while this follows the standard template <typename Element> conventions of OpenFHE, it's really only designed to work for DCRTPoly...
template <typename Element>
class HeraclesTracer;

template <typename Element>
class HeraclesFunctionTracer : public FunctionTracer<Element>
{
public:
    HeraclesFunctionTracer(const std::string &func, HeraclesTracer<Element> *tracer) :
        m_tracer(tracer)
    {
        m_currentInstruction = heracles::fhe_trace::Instruction();

        // TODO: we should differentiate between high-level ops and low-level ops
        // and use eval_op name for higher level ops that created several lower-level ops
        // but that also requires adding a bit of scoping logic in HeraclesTracer
        m_currentInstruction.set_evalop_name(func); // Store the original function name

        m_currentInstruction.set_op(m_tracer->getHeraclesInstruction(func));

        auto cc = m_tracer->getCryptoContext();
        if (cc->getSchemeId() != CKKSRNS_SCHEME)
        {
            // FIXME: set this based on the plaintext algebra being used
            m_currentInstruction.set_plaintext_index(0);
        }
    }

    ~HeraclesFunctionTracer() override
    {
        // Transfer collected operands and parameters to the instruction
        for (const auto &source : m_sources)
        {
            m_currentInstruction.mutable_args()->add_srcs()->CopyFrom(source);
        }

        for (const auto &dest : m_destinations)
        {
            m_currentInstruction.mutable_args()->add_dests()->CopyFrom(dest);
        }

        // Transfer parameters using the stored names
        for (size_t i = 0; i < m_parameters.size() && i < m_parameterNames.size(); ++i)
        {
            (*m_currentInstruction.mutable_args()->mutable_params())[m_parameterNames[i]].CopyFrom(m_parameters[i]);
        }

        // Finalize the instruction and add it to the tracer
        m_tracer->addInstruction(m_currentInstruction);
    }

    // Input registration methods

    /// Register data with in/out flag to avoid duplication of conversion logic
    void registerData(std::vector<Element> elements, std::string name, bool isOutput = false)
    {
        if (elements.empty())
            throw std::runtime_error("Cannot register empty data.");

        // Use the semantic name (ct, pt, sk, pk, etc.) instead of always "dcrtpoly"
        std::string id = m_tracer->getUniqueObjectId(elements, name);

        // Create OperandObject (name, num_rns, order)
        auto operand = heracles::fhe_trace::OperandObject();
        operand.set_symbol_name(id);
        operand.set_num_rns(elements[0].GetNumOfElements());
        operand.set_order(elements.size());

        // Add to appropriate member variable for later processing in destructor
        if (isOutput)
        {
            m_destinations.push_back(operand);
            m_tracer->trackOutput(id);
        }
        else
        {
            m_sources.push_back(operand);
            // Check for orphaned inputs (objects that weren't registered as outputs)
            m_tracer->checkInput(id, m_currentInstruction.op());
        }

        // Add to TestVector: Convert DCRTPoly to protobuf format
        auto data     = heracles::data::Data();
        auto dcrtpoly = data.mutable_dcrtpoly();

        // Set whether the polynomial is in NTT form
        dcrtpoly->set_in_ntt_form(elements[0].GetFormat() == Format::EVALUATION);

        for (const auto &element : elements)
        {
            auto poly = dcrtpoly->add_polys();
            convertDCRTPolyToProtobuf(poly, element);
        }

        m_tracer->storeData(id, data);
    }

    // Helper for single elements
    void registerData(Element element, std::string name, bool isOutput = false)
    {
        registerData(std::vector<Element>(1, element), name, isOutput);
    }

    void registerInput(Ciphertext<Element> ciphertext, std::string name, bool isMutable) override
    {
        registerData(ciphertext->GetElements(), name.empty() ? "ciphertext" : name);
    }

    void registerInput(ConstCiphertext<Element> ciphertext, std::string name, bool isMutable) override
    {
        registerData(ciphertext->GetElements(), name.empty() ? "ciphertext" : name);
    }

    void registerInput(Plaintext plaintext, std::string name, bool isMutable) override
    {
        registerData(plaintext->GetElement<Element>(), name.empty() ? "plaintext" : name);
    }

    void registerInput(ConstPlaintext plaintext, std::string name, bool isMutable) override
    {
        registerData(plaintext->GetElement<Element>(), name.empty() ? "plaintext" : name);
    }

    void registerInput(const PublicKey<Element> publicKey, std::string name, bool isMutable) override
    {
        registerData(publicKey->GetPublicElements(), name.empty() ? "publickey" : name, false);
    }

    void registerInput(const PrivateKey<Element> privateKey, std::string name, bool isMutable) override
    {
        registerData(privateKey->GetPrivateElement(), name.empty() ? "secretkey" : name, false);
    }

    void registerInput(const EvalKey<Element> evalKey, std::string name, bool isMutable) override
    {
        name = name.empty() ? "evalkey" : name;
        // EvalKey doesn't have GetElement method, just skip for now
        // FIXME: implement proper EvalKey extraction
        std::cout << "Warning: EvalKey registration not yet implemented in HeraclesTracer." << std::endl;
        (void)evalKey; // Suppress unused parameter warning
    }

    void registerInput(const PlaintextEncodings encoding, std::string name, bool isMutable) override
    {
        std::string encodingStr;
        switch (encoding)
        {
        case PlaintextEncodings::COEF_PACKED_ENCODING:
            encodingStr = "COEF_PACKED_ENCODING";
            break;
        case PlaintextEncodings::PACKED_ENCODING:
            encodingStr = "PACKED_ENCODING";
            break;
        case PlaintextEncodings::STRING_ENCODING:
            encodingStr = "STRING_ENCODING";
            break;
        case PlaintextEncodings::CKKS_PACKED_ENCODING:
            encodingStr = "CKKS_PACKED_ENCODING";
            break;
        default:
            encodingStr = "UNKNOWN_ENCODING";
            break;
        }
        addParameter(name.empty() ? "encoding" : name, encodingStr, "string");
    }

    void registerInput(const std::vector<int64_t> &values, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "int64_vector" : name, values.size(), "uint64");
    }

    void registerInput(const std::vector<int32_t> &values, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "int32_vector" : name, values.size(), "uint32");
    }

    void registerInput(const std::vector<uint32_t> &values, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "uint32_vector" : name, values.size(), "uint32");
    }

    void registerInput(const std::vector<double> &values, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "double_vector" : name, values.size(), "uint64");
    }

    void registerInput(double value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "double" : name, value, "double");
    }

    void registerInput(std::complex<double> value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "complex_real" : name + "_real", value.real(), "double");
        addParameter(name.empty() ? "complex_imag" : name + "_imag", value.imag(), "double");
    }

    void registerInput(const std::vector<std::complex<double>> &values, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "complex_vector" : name, values.size(), "uint64");
    }

    void registerInput(int64_t value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "int64" : name, value, "int64");
    }

    void registerInput(size_t value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "size_t" : name, value, "uint64");
    }

    void registerInput(bool value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "bool" : name, value ? "true" : "false", "string");
    }

    void registerInput(const std::string &value, std::string name, bool isMutable) override
    {
        addParameter(name.empty() ? "string" : name, value, "string");
    }

    void registerInput(const std::shared_ptr<std::map<uint32_t, EvalKey<Element>>> &evalKeyMap, std::string name,
                       bool isMutable) override
    {
        size_t mapSize = evalKeyMap ? evalKeyMap->size() : 0;
        addParameter(name.empty() ? "eval_key_map_size" : name + "_size", mapSize, "uint64");
    }

    void registerInput(void *ptr, std::string name, bool isMutable) override
    {
        throw std::runtime_error("HERACLES tracing does not support registering non-typed inputs.");
    }

    // Output registration methods
    Ciphertext<Element> registerOutput(Ciphertext<Element> ciphertext, std::string name) override
    {
        if (ciphertext && ciphertext->GetElements().size() > 0)
        {
            registerData(ciphertext->GetElements(), name.empty() ? "ciphertext" : name, true); // true = output
        }
        return ciphertext;
    }

    ConstCiphertext<Element> registerOutput(ConstCiphertext<Element> ciphertext, std::string name) override
    {
        if (ciphertext && ciphertext->GetElements().size() > 0)
        {
            registerData(ciphertext->GetElements(), name.empty() ? "ciphertext" : name, true); // true = output
        }
        return ciphertext;
    }

    Plaintext registerOutput(Plaintext plaintext, std::string name) override
    {
        if (plaintext)
        {
            // Convert single element to vector for registerData
            std::vector<Element> elements = { plaintext->GetElement<Element>() };
            registerData(elements, name.empty() ? "plaintext" : name, true); // true = output
        }
        return plaintext;
    }

    KeyPair<Element> registerOutput(KeyPair<Element> keyPair, std::string name) override
    {
        if (keyPair.publicKey)
            registerData(keyPair.publicKey->GetPublicElements(), "publickey", true);
        if (keyPair.secretKey)
            registerData(keyPair.secretKey->GetPrivateElement(), "secretkey", true);
        return keyPair;
    }

    EvalKey<Element> registerOutput(EvalKey<Element> evalKey, std::string name) override
    {
        if (evalKey)
        {
            // Convert evaluation key elements to vector for registerData
            std::vector<Element> elements = evalKey->GetBVector(); // Get the B vector
            registerData(elements, name.empty() ? "evalkey" : name, true); // true = output
        }
        return evalKey;
    }

    std::vector<EvalKey<Element>> registerOutput(std::vector<EvalKey<Element>> evalKeys, std::string name) override
    {
        // TODO: registerData this, too
        return evalKeys;
    }

    std::vector<Ciphertext<Element>> registerOutput(std::vector<Ciphertext<Element>> ciphertexts,
                                                    std::string name) override
    {
        for (auto &ct : ciphertexts)
        {
            registerOutput(ct, name);
        }
        return ciphertexts;
    }

    std::shared_ptr<std::map<uint32_t, EvalKey<Element>>> registerOutput(
        std::shared_ptr<std::map<uint32_t, EvalKey<Element>>> evalKeyMap, std::string name) override
    {
        // TODO: registerData this, too
        return evalKeyMap;
    }

    PublicKey<Element> registerOutput(PublicKey<Element> publicKey, std::string name) override
    {
        // TODO: registerData this, too
        return publicKey;
    }

    PrivateKey<Element> registerOutput(PrivateKey<Element> privateKey, std::string name) override
    {
        // TODO: registerData this, too
        return privateKey;
    }

    std::string registerOutput(const std::string &value, std::string name) override
    {
        // TODO: registerData this, too
        return value;
    }

    Element registerOutput(Element element, std::string name) override
    {
        // TODO: registerData this, too
        return element;
    }

private:
    HeraclesTracer<Element> *m_tracer;
    heracles::fhe_trace::Instruction m_currentInstruction;

    // We record the args and params in case some ops require reordering them
    std::vector<heracles::fhe_trace::OperandObject> m_sources;
    std::vector<heracles::fhe_trace::OperandObject> m_destinations;
    std::vector<heracles::fhe_trace::Parameter> m_parameters;
    std::vector<std::string> m_parameterNames; // Parameter names corresponding to m_parameters

    /// Helper to extract SSA ID from objects for HERACLES tracing (delegated to HeraclesTracer)
    template <typename T>
    std::string getObjectId(T obj, const std::string &type)
    {
        return m_tracer->getUniqueObjectId(obj, type);
    }

    /// Helper to create HERACLES OperandObject for ciphertexts/plaintexts
    void setHERACLESOperandObject(heracles::fhe_trace::OperandObject *opObj, const std::string &objectId,
                                  size_t numRNS = 0, size_t order = 1)
    {
        opObj->set_symbol_name(objectId);
        opObj->set_num_rns(numRNS);
        opObj->set_order(order);
    }

    /// Helper to add parameter to HERACLES instruction
    template <typename T>
    void addParameter(const std::string &name, const T &value, const std::string &type)
    {
        heracles::fhe_trace::Parameter param;
        std::stringstream ss;
        ss << value;
        param.set_value(ss.str());

        // Set parameter type based on type string
        std::string upperType = type;
        std::transform(upperType.begin(), upperType.end(), upperType.begin(), ::toupper);

        if (upperType == "DOUBLE")
        {
            param.set_type(heracles::fhe_trace::ValueType::DOUBLE);
        }
        else if (upperType == "FLOAT")
        {
            param.set_type(heracles::fhe_trace::ValueType::FLOAT);
        }
        else if (upperType == "INT32")
        {
            param.set_type(heracles::fhe_trace::ValueType::INT32);
        }
        else if (upperType == "INT64")
        {
            param.set_type(heracles::fhe_trace::ValueType::INT64);
        }
        else if (upperType == "UINT32")
        {
            param.set_type(heracles::fhe_trace::ValueType::UINT32);
        }
        else if (upperType == "UINT64")
        {
            param.set_type(heracles::fhe_trace::ValueType::UINT64);
        }
        else
        {
            param.set_type(heracles::fhe_trace::ValueType::STRING);
        }

        // Store in member variables with name for later processing
        m_parameterNames.push_back(name);
        m_parameters.push_back(param);
    }

    /// Helper to convert DCRTPoly to HERACLES protobuf format
    void convertDCRTPolyToProtobuf(heracles::data::Polynomial *proto_poly, const Element &dcrtpoly)
    {
        const auto &elems = dcrtpoly.GetAllElements();
        proto_poly->set_in_openfhe_evaluation((dcrtpoly.GetFormat() == Format::EVALUATION));

        for (size_t l = 0; l < dcrtpoly.GetNumOfElements(); ++l)
        {
            size_t poly_degree = elems[l].GetLength();
            auto elem_vals     = elems[l].GetValues();
            auto rns_poly_pb   = proto_poly->add_rns_polys();

            std::vector<uint32_t> v_coeffs(poly_degree);
            for (size_t j = 0; j < poly_degree; ++j)
            {
                v_coeffs[j] = elem_vals[j].ConvertToInt();
            }

            *rns_poly_pb->mutable_coeffs() = { v_coeffs.begin(), v_coeffs.end() };
            rns_poly_pb->set_modulus(elems[l].GetModulus().ConvertToInt());
        }
    }
};

/// HERACLES Protobuf Tracing implementation
/// Generates protobuf traces compatible with the HERACLES project
template <typename Element>
class HeraclesTracer : public Tracer<Element>
{
public:
    HeraclesTracer(const std::string &filename = "openfhe-heracles-trace", const CryptoContext<Element> &cc = nullptr, bool warnOnUnregisteredInputs = true) :
        m_filename(filename), m_context(cc), m_warnOnUnregisteredInputs(warnOnUnregisteredInputs)
    {
        if (!cc)
        {
            throw std::runtime_error("HeraclesTracer requires a valid CryptoContext - cannot be null");
        }
        _initializeTrace();
    }

    ~HeraclesTracer() override = default;

    // Override the virtual createFunctionTracer method (required by new API)
    std::unique_ptr<FunctionTracer<Element>> createFunctionTracer(std::string func) override
    {
        // Check if this the func matches a no_emit_prefix
        // If yes, return a null tracer that does not do anything
        for (const auto &prefix : no_emit_prefixes)
            if (func.find(prefix) == 0)
                return std::make_unique<NullFunctionTracer<Element>>();

        // Otherwise, create a real tracer that will emit instructions
        return std::make_unique<HeraclesFunctionTracer<Element>>(func, this);
    }

    CryptoContext<Element> getCryptoContext()
    {
        return m_context;
    }

    /// Generate unique object ID using SimpleTracer-style logic
    template <typename T>
    std::string getUniqueObjectId(T obj, const std::string &type)
    {
        // Serialize and hash the object for uniqueness detection
        std::stringstream serialStream;
        Serial::Serialize(obj, serialStream, SerType::BINARY);
        const std::string hash = HashUtil::HashString(serialStream.str());

        // Check if we already have a unique ID for this hash
        auto hashIt = m_uniqueID.find(hash);
        if (hashIt != m_uniqueID.end())
        {
            // Object already seen - reuse existing ID
            return hashIt->second;
        }

        // Generate new ID using counter
        size_t &counter  = m_counters[type];
        std::string id   = type + "_" + std::to_string(++counter);
        m_uniqueID[hash] = id;
        return id;
    }

    void addInstruction(const heracles::fhe_trace::Instruction &instruction)
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_FHETrace->add_instructions()->CopyFrom(instruction);
    }

    /// Track an object ID as a known output
    void trackOutput(const std::string &objectId)
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        m_knownOutputs.insert(objectId);
    }

    /// Check if an input object ID was previously registered as an output
    /// Prints a warning if the object appears to be "orphaned" (not from any traced output)
    void checkInput(const std::string &objectId, const std::string &operationName)
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        if (m_warnOnUnregisteredInputs && m_knownOutputs.find(objectId) == m_knownOutputs.end())
        {
            std::cout << "WARNING: Object '" << objectId << "' used as input in operation '" << operationName
                      << "' but was never registered as output of any traced operation." << std::endl;
            std::cout << "This is normal if only tracing server-side code (and indicates this is a client input),"
                      << " but may indicate missing internal tracing logic if tracing client and server side code." << std::endl;
        }
    }

    /// Store data for test vector
    void storeData(const std::string &objectId, const heracles::data::Data &data)
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        (*m_TestVector->mutable_sym_data_map())[objectId] = data;
    }

    /// Save trace to file in binary format
    void saveBinaryTrace()
    {
        std::lock_guard<std::mutex> lock(m_mutex);

        heracles::fhe_trace::store_trace(m_filename + ".bin", *m_FHETrace);

        // Create manifest for the binary files
        heracles::data::hdf_manifest manifest;

        // Store context and test vector with manifest
        heracles::data::store_hec_context(&manifest, m_filename + "_context.bin", *m_FHEContext);
        heracles::data::store_testvector(&manifest, m_filename + "_testvector.bin", *m_TestVector);

        // Store the combined data trace
        heracles::data::store_data_trace(m_filename + "_data.bin", *m_FHEContext, *m_TestVector);

        // Generate the manifest file
        heracles::data::generate_manifest(m_filename + "_manifest.txt", manifest);
    }

    /// Save trace to file in JSON format
    void saveJsonTrace()
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        heracles::fhe_trace::store_json_trace(m_filename + ".json", *m_FHETrace);
        heracles::data::store_hec_context_json(m_filename + "_context.json", *m_FHEContext);
        heracles::data::store_testvector_json(m_filename + "_testvector.json", *m_TestVector);
        // Note: the combined data trace object is not available in *.json
    }

    std::string getHeraclesInstruction(std::string functionName) const
    {
        // No mutex lock, since we're just reading a const member
        // Check the map, if not in there, return the functionName
        // Note: this is using prefix matching!
        for (const auto &[key, value] : op_name_map)
            if (functionName.find(key) == 0)
                return value;
        return functionName;
    }

private:
    /// Guards access to member variables for accesses by FunctionTracer(s)
    mutable std::mutex m_mutex;

    // ID management (accessible by HeraclesFunctionTracer for naming logic)
    std::unordered_map<std::string, std::string> m_uniqueID; // hash -> human-readable ID
    std::unordered_map<std::string, size_t> m_counters; // type -> counter

    // Track known output IDs to detect missing tracing calls
    std::unordered_set<std::string> m_knownOutputs; // object IDs that have been registered as outputs

    std::string m_filename; // Filename basis to use. Will be extended with _data and *.bin/*.json
    CryptoContext<Element> m_context; // CryptoContext for the current trace
    bool m_warnOnUnregisteredInputs; // Whether to warn on unregistered inputs

    // Generated traces (nullptr until tracing is finished)
    std::unique_ptr<heracles::fhe_trace::Trace> m_FHETrace   = nullptr;
    std::unique_ptr<heracles::data::FHEContext> m_FHEContext = nullptr;
    std::unique_ptr<heracles::data::TestVector> m_TestVector = nullptr;

    /// Instructions to skip emission for (but still trace nested instructions)
    /// WARNING: the match is on the PREFIX of the instruction name,
    /// so LeveledSHERNS::AdjustForMultInPlace will match
    /// LeveledSHERNS::AdjustForMultInPlace(ciphertext1, ciphertext2)
    /// but also LeveledSHERNS::AdjustForMultInPlace(ciphertext, plaintext)
    /// Note: This means that InPlace versions are also matched, e.g.,
    /// LeveledSHERNS::EvalAdd will also match LeveledSHERNS::EvalAddInPlace!
    const std::unordered_set<std::string> no_emit_prefixes = {
        // Ignore all CryptoContext high-level wrappers
        "CryptoContext::",
        // Automagic Adjustment Wrappers
        "LeveledSHEBase::AdjustForMult",
        "LeveledSHERNS::AdjustForMult",
        "LeveledSHERNS::AdjustForAddOrSub",
        "LeveledSHECKKSRNS::AdjustLevelsAndDepth", // also covers "..ToOne" version
        // Multiplication Wrappers
        "LeveledSHEBase::EvalMult",
        "LeveledSHERNS::EvalMult",
        "LeveledSHECKKSRNS::EvalMult(", // We do want LeveledSHECKKSRNS::EvalMultCore
        "LeveledSHECKKSRNS::EvalMultInPlace(", // so we can't just match on EvalMult!
        // Addition/Subtraction Wrappers
        "LeveledSHERNS::EvalAdd(", // Again, we want the ::...Core version
        "LeveledSHERNS::EvalAddInPlace(",
        "LeveledSHERNS::EvalSub(", // Again, we want the ::...Core version
        "LeveledSHERNS::EvalSubInPlace(",
    };

    /// Mapping from OpenFHE function name (prefix) to HERACLES instruction name
    /// WARNING: this is also prefix match, so it will match the beginning of the function name
    const std::unordered_map<std::string, std::string> op_name_map = {
        // Addition
        { "LeveledSHEBase::EvalAddCore(Ciphertext,Ciphertext)", "add" },
        { "LeveledSHEBase::EvalAddCoreInPlace(Ciphertext,Ciphertext)", "add" },
        { "LeveledSHEBase::EvalAddCore(Ciphertext,Plaintext)", "add" },
        { "LeveledSHEBase::EvalAddCoreInPlace(Ciphertext,Plaintext)", "add" },
        // Subtraction
        { "LeveledSHEBase::EvalSubCore(Ciphertext,Ciphertext)", "sub" },
        { "LeveledSHEBase::EvalSubCoreInPlace(Ciphertext,Ciphertext)", "sub" },
        { "LeveledSHEBase::EvalSubCore(Ciphertext,Plaintext)", "sub" },
        { "LeveledSHEBase::EvalSubCoreInPlace(Ciphertext,Plaintext)", "sub" },
        // Multiplication (scheme-specific)
        { "LeveledSHECKKSRNS::EvalMultCore(Ciphertext,Ciphertext)", "mul" },
        { "LeveledSHECKKSRNS::EvalMultCoreInPlace(ciphertext, ciphertext)", "mul" },
        { "LeveledSHECKKSRNS::EvalMultCore(Ciphertext,Plaintext)", "mul" },
        { "LeveledSHECKKSRNS::EvalMultCoreInPlace(Ciphertext,Plaintext)", "mul" },
        { "LeveledSHECKKSRNS::EvalMultCore(Ciphertext,double)", "muli" },
        { "LeveledSHECKKSRNS::EvalMultCoreInPlace(Ciphertext,double)", "muli" },
        // Also map the high-level wrappers in case they slip through
        { "LeveledSHECKKSRNS::EvalMult(Ciphertext,double)", "muli" },
        { "LeveledSHECKKSRNS::EvalMultInPlace(Ciphertext,double)", "muli" },
        // Modulus Reduction / Rescale
        { "LeveledSHECKKSRNS::ModReduceInternal", "rescale" },
        // Rotation
        { "LeveledSHEBase::EvalAutomorphism", "rotate" }

    };

    void _initializeTrace()
    {
        m_FHETrace   = std::make_unique<heracles::fhe_trace::Trace>();
        m_TestVector = std::make_unique<heracles::data::TestVector>();
        m_FHEContext = std::make_unique<heracles::data::FHEContext>();
        _initializeContext();

        m_FHETrace->set_scheme(m_FHEContext->scheme());
        m_FHETrace->set_n(m_FHEContext->n());
        m_FHETrace->set_key_rns_num(m_FHEContext->key_rns_num());
        m_FHETrace->set_q_size(m_FHEContext->q_size());
        m_FHETrace->set_dnum(m_FHEContext->digit_size());
        m_FHETrace->set_alpha(m_FHEContext->alpha());
    }

    void
    _initializeContext()
    {
        if (!m_context)
        {
            throw std::runtime_error("No CryptoContext provided for HERACLES tracing");
        }

        auto cc_rns = std::dynamic_pointer_cast<CryptoParametersRNS>(m_context->GetCryptoParameters());
        if (!cc_rns)
            throw std::runtime_error("HERACLES requires RNS parameters.");
        auto key_rns = cc_rns->GetParamsQP()->GetParams();

        auto scheme = m_context->getSchemeId();
        switch (scheme)
        {
        case SCHEME::CKKSRNS_SCHEME:
        {
            m_FHEContext->set_scheme(heracles::common::SCHEME_CKKS);
            // Add CKKS-specific information
            // FIXME: set_has_ckks_info() is private, need to find correct way to set this
            // m_FHEContext->set_has_ckks_info();
            auto ckks_info = m_FHEContext->mutable_ckks_info();
            size_t sizeQ   = m_context->GetElementParams()->GetParams().size();
            for (size_t i = 0; i < sizeQ; ++i)
            {
                ckks_info->add_scaling_factor_real(cc_rns->GetScalingFactorReal(i));
                if (i < sizeQ - 1)
                    ckks_info->add_scaling_factor_real_big(cc_rns->GetScalingFactorRealBig(i));
            }

            // Populate metadata_extra map with key-switching parameters
            auto metadata_extra = ckks_info->mutable_metadata_extra();

            // Get key parameters
            uint32_t dnum      = cc_rns->GetNumPartQ(); // number of digits
            uint32_t alpha     = cc_rns->GetNumPerPartQ(); // towers per digit
            auto elementParams = m_context->GetElementParams()->GetParams();
            size_t sizeP       = key_rns.size() - sizeQ; // number of special primes

            // Helper to create string keys for multi-index metadata
            auto toStrKey = [](std::initializer_list<uint32_t> indices) {
                std::string key;
                for (auto idx : indices)
                {
                    if (!key.empty())
                        key += "_";
                    key += std::to_string(idx);
                }
                return key;
            };

            // 1. Compute partQHatInvModq_{i}_{j} = (Q/Qi)^-1 mod qj
            // This is NOT available from OpenFHE API, must compute manually
            for (uint32_t i = 0; i < dnum; ++i)
            {
                for (uint32_t j = 0; j < sizeQ; ++j)
                {
                    uint32_t value = 0;

                    // Check if qj is in digit i
                    uint32_t digitStart = i * alpha;
                    uint32_t digitEnd   = std::min((i + 1) * alpha, static_cast<uint32_t>(sizeQ));

                    if (j < digitStart || j >= digitEnd)
                    {
                        // qj is not in Qi, so we need to compute (Q/Qi)^-1 mod qj
                        // Q/Qi is the product of all primes NOT in digit i

                        // Get modulus qj
                        auto qj = elementParams[j]->GetModulus();

                        // Compute QHati mod qj (product of primes not in digit i, taken mod qj at each step)
                        // We need to be careful to reduce mod qj at each step to avoid overflow
                        NativeInteger qHatiModqj = 1;
                        for (uint32_t k = 0; k < sizeQ; ++k)
                        {
                            if (k < digitStart || k >= digitEnd)
                            {
                                // For k != j, multiply by (qk mod qj)
                                // For k == j, this would give 0, so skip it
                                if (k != j)
                                {
                                    auto qk               = elementParams[k]->GetModulus();
                                    NativeInteger qkModqj = qk.Mod(qj);
                                    qHatiModqj            = qHatiModqj.ModMul(qkModqj, qj);
                                }
                            }
                        }

                        // Compute modular inverse only if qHatiModqj is non-zero
                        if (qHatiModqj != 0)
                        {
                            value = qHatiModqj.ModInverse(qj).ConvertToInt();
                        }
                        // If qHatiModqj is 0, value remains 0
                    }
                    // If j is in digit i, value remains 0

                    (*metadata_extra)["partQHatInvModq_" + toStrKey({ i, j })] = value;
                }
            }

            // 2. Extract partQlHatInvModq from OpenFHE API
            for (uint32_t i = 0; i < dnum; ++i)
            {
                uint32_t digitSize = i < (dnum - 1) ? alpha : sizeQ - alpha * (dnum - 1);
                for (uint32_t j = 0; j < digitSize; ++j)
                {
                    auto &values = cc_rns->GetPartQlHatInvModq(i, j);
                    for (uint32_t l = 0; l < values.size() && l <= j; ++l)
                    {
                        (*metadata_extra)["partQlHatInvModq_" + toStrKey({ i, j, l })] =
                            values[l].ConvertToInt();
                    }
                }
            }

            // 3. Extract partQlHatModp from OpenFHE API
            for (uint32_t i = 0; i < sizeQ; ++i)
            {
                uint32_t beta = std::ceil(static_cast<float>(i + 1) / static_cast<float>(alpha));
                for (uint32_t j = 0; j < beta; ++j)
                {
                    uint32_t digitSize = j < beta - 1 ? alpha : (i + 1) - alpha * (beta - 1);
                    auto &matrix       = cc_rns->GetPartQlHatModp(i, j);
                    for (uint32_t l = 0; l < digitSize && l < matrix.size(); ++l)
                    {
                        for (uint32_t s = 0; s < matrix[l].size(); ++s)
                        {
                            (*metadata_extra)["partQlHatModp_" + toStrKey({ i, j, l, s })] =
                                matrix[l][s].ConvertToInt();
                        }
                    }
                }
            }

            // 4. Extract pInvModq from OpenFHE API
            auto &pInvModq = cc_rns->GetPInvModq();
            for (uint32_t i = 0; i < sizeQ && i < pInvModq.size(); ++i)
            {
                (*metadata_extra)["pInvModq_" + std::to_string(i)] = pInvModq[i].ConvertToInt();
            }

            // 5. Extract pModq from OpenFHE API
            auto &pModq = cc_rns->GetPModq();
            for (uint32_t i = 0; i < sizeQ && i < pModq.size(); ++i)
            {
                (*metadata_extra)["pModq_" + std::to_string(i)] = pModq[i].ConvertToInt();
            }

            // 6. Extract pHatInvModp from OpenFHE API
            auto &pHatInvModp = cc_rns->GetPHatInvModp();
            for (uint32_t i = 0; i < sizeP && i < pHatInvModp.size(); ++i)
            {
                (*metadata_extra)["pHatInvModp_" + std::to_string(i)] = pHatInvModp[i].ConvertToInt();
            }

            // 7. Extract pHatModq from OpenFHE API - P/pi mod qj
            auto &pHatModq = cc_rns->GetPHatModq();
            for (uint32_t i = 0; i < sizeP && i < pHatModq.size(); ++i)
            {
                for (uint32_t j = 0; j < sizeQ && j < pHatModq[i].size(); ++j)
                {
                    (*metadata_extra)["pHatModq_" + toStrKey({ i, j })] = pHatModq[i][j].ConvertToInt();
                }
            }

            // 8. Compute rescale metadata - qlInvModq_{i}_{j} = q_{sizeQ-(i+1)}^{-1} mod qj
            for (uint32_t i = 0; i < sizeQ - 1; ++i)
            {
                // q_l is the prime to be dropped (from the end)
                uint32_t qlIndex = sizeQ - (i + 1);
                auto ql          = elementParams[qlIndex]->GetModulus();

                for (uint32_t j = 0; j < sizeQ - (i + 1); ++j)
                {
                    auto qj = elementParams[j]->GetModulus();
                    // Compute q_l^{-1} mod qj
                    NativeInteger qlModqj = ql.Mod(qj);
                    uint32_t value        = 0;
                    if (qlModqj != 0)
                    {
                        value = qlModqj.ModInverse(qj).ConvertToInt();
                    }
                    (*metadata_extra)["qlInvModq_" + toStrKey({ i, j })] = value;
                }
            }

            // 9. Extract QlQlInvModqlDivqlModq from OpenFHE API
            for (uint32_t i = 0; i < sizeQ - 1; ++i)
            {
                auto &values = cc_rns->GetQlQlInvModqlDivqlModq(i);
                for (uint32_t j = 0; j < values.size() && j < sizeQ - (i + 1); ++j)
                {
                    (*metadata_extra)["QlQlInvModqlDivqlModq_" + toStrKey({ i, j })] = values[j].ConvertToInt();
                }
            }

            // 10. Add boot_correction placeholder - this is related to bootstrapping
            // OpenFHE 1.3 doesn't expose this directly, using a reasonable default
            // This may need to be adjusted based on specific bootstrapping parameters
            (*metadata_extra)["boot_correction"] = 0; // Default value when bootstrapping is not used
        }
        break;
        case SCHEME::BGVRNS_SCHEME:
        {
            m_FHEContext->set_scheme(heracles::common::SCHEME_BGV);
            // BGV not fully supported yet
        }
        break;
        case SCHEME::BFVRNS_SCHEME:
        {
            m_FHEContext->set_scheme(heracles::common::SCHEME_BFV);
            // BFV not fully supported yet
        }
        break;
        default:
            throw std::runtime_error("Unsupported scheme for HERACLES tracing");
        }

        // TODO: check in old tracing code what these should be set to!
        auto poly_degree = m_context->GetRingDimension();
        m_FHEContext->set_n(poly_degree);
        m_FHEContext->set_key_rns_num(key_rns.size());
        m_FHEContext->set_alpha(cc_rns->GetNumPerPartQ());
        m_FHEContext->set_digit_size(cc_rns->GetNumPartQ());
        for (const auto &parms : key_rns)
        {
            auto q_i = parms->GetModulus();
            m_FHEContext->add_q_i(q_i.ConvertToInt());

            auto psi_i = RootOfUnity<NativeInteger>(poly_degree * 2, parms->GetModulus());
            m_FHEContext->add_psi(psi_i.ConvertToInt());
        }
        m_FHEContext->set_q_size(m_context->GetElementParams()->GetParams().size());
        m_FHEContext->set_alpha(cc_rns->GetNumPerPartQ());
    }
};

} // namespace lbcrypto

#endif // ENABLE_TRACER

#endif // P_ISA_TOOLS_DATA_FORMATS_TRACERS_OPENFHE_TRACER_H_
