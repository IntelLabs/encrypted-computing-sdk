// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include "google/protobuf/util/json_util.h"
#include "heracles/heracles_data_formats.h"
#include "heracles/heracles_proto.h"

void fhe_trace_tests()
{
    // Create sample trace
    heracles::fhe_trace::Trace trace;
    // - context
    trace.set_scheme(heracles::common::SCHEME_BGV);
    trace.set_key_rns_num(70);
    trace.set_n(16384);
    // - first instruction
    auto negate = trace.add_instructions();
    negate->set_op("NEGATE");
    negate->set_plaintext_index(2);
    auto neg_args = negate->mutable_args();
    auto neg_args_dest = neg_args->add_dests();
    neg_args_dest->set_symbol_name("t1");
    neg_args_dest->set_num_rns(5);
    neg_args_dest->set_order(2);
    auto neg_args_src = neg_args->add_srcs();
    neg_args_src->set_symbol_name("in1");
    neg_args_src->set_num_rns(5);
    neg_args_src->set_order(2);
    // - second instruction
    auto add = trace.add_instructions();
    add->set_op("ADD");
    add->set_plaintext_index(2);
    auto add_args = add->mutable_args();
    heracles::fhe_trace::OperandObject *add_args_dest = new heracles::fhe_trace::OperandObject();
    add_args_dest->set_symbol_name("out1");
    add_args_dest->set_num_rns(5);
    add_args_dest->set_order(2);
    // add_args->add_dests()->CopyFrom(*add_args_dest);
    add_args->add_dests()->CopyFrom(*add_args_dest);
    add_args->add_srcs()->CopyFrom(add_args->dests(0));
    add_args->mutable_srcs(0)->set_symbol_name("t1");
    add_args->add_srcs()->CopyFrom(add_args->dests(0));
    add_args->mutable_srcs(1)->set_symbol_name("in2");

    // display it ..
    std::cout << "debug string: " << trace.DebugString() << std::endl;
    std::string json;
    auto rc = google::protobuf::util::MessageToJsonString(trace, &json);
    std::cout << "json: " << json << std::endl;

    // accessing enums as default strings and as our own version ..
    auto scheme = trace.scheme();
    std::cout << "scheme: as-num=" << scheme
              << " / as-default-string=" << heracles::common::Scheme_descriptor()->FindValueByNumber(scheme)->name()
              << " / as-friendly-string="
              << heracles::common::Scheme_descriptor()->value(scheme)->options().GetExtension(
                     heracles::common::string_name)
              << std::endl;

    // serialize it to file
    if (!heracles::fhe_trace::store_trace("test.program_trace", trace))
    {
        std::cerr << "Could not serialize" << std::endl;
        exit(1);
    }

    // deserialize it from file
    heracles::fhe_trace::Trace deserialized_trace;
    trace = heracles::fhe_trace::load_trace("test.program_trace");

    std::cout << "debug string: " << deserialized_trace.DebugString() << std::endl;
}

void map_tests()
{
    // serialize/deserialize of the input map objects ...
    heracles::data::DataPolynomials polys;
    auto poly_map = polys.mutable_data()->mutable_sym_poly_map();
    auto key = "key";
    (*poly_map)[key].add_coeffs(1);
    (*poly_map)[key].add_coeffs(2);
    auto *coeffs = ((*poly_map)[key].mutable_coeffs());
    coeffs->Resize(8, -1);
    // coeffs->Add(3);
    coeffs->at(2) = -3;
    // coeffs->Add(4);
    (*poly_map)[key].set_coeffs(3, -4);

    std::cout << "debug string: " << polys.DebugString() << std::endl;
    std::string json;
    auto rc = google::protobuf::util::MessageToJsonString(polys, &json);
    std::cout << "json: " << json << std::endl;

    // serialize to buffer ...
    // std::byte would be nicer but had trouble compiling with -std=c++17
    std::vector<unsigned char> buf(polys.ByteSizeLong());
    if (!polys.SerializeToArray(buf.data(), buf.size()))
    {
        std::cerr << "Could not serialize" << std::endl;
        exit(1);
    }

    // .. and deserialize it to new object
    heracles::data::DataPolynomials new_polys;
    if (!new_polys.ParseFromArray(buf.data(), buf.size()))
    {
        std::cerr << "Could not serialize" << std::endl;
        exit(1);
    }

    std::cout << "new: " << new_polys.DebugString() << std::endl;
}

void cpp_data_tests()
{
    heracles::data::FHEContext context;
    heracles::data::TestVector testvector;
    context.set_scheme(heracles::common::SCHEME_BGV);
    heracles::data::store_data_trace("test.data_trace", context, testvector);

    auto [new_context, new_testvector] = heracles::data::load_data_trace("test.data_trace");
    std::cout << "COMPLETE: cpp_data_tests" << std::endl;
}

int main(int /*argc*/, const char * /*argv*/[])
{
    map_tests();
    fhe_trace_tests();
    cpp_data_tests();
}
