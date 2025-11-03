// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/data/io.h"
#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <google/protobuf/util/json_util.h>
#include <iostream>

namespace heracles::data
{
hdf_manifest parse_manifest(const std::string &filename)
{
    hdf_manifest manifest;
    std::ifstream file(filename);

    if (!file.is_open())
    {
        throw std::runtime_error("Manifest file not found: " + filename);
    }

    std::string header, current_line;
    auto trim = [](const std::string &line) {
        std::string res = line;
        res.erase(std::remove_if(res.begin(), res.end(), isspace), res.end());
        return res;
    };

    std::string cur_field = "";
    bool found_first_field = false;
    int linenum = 0;
    while (std::getline(file, current_line))
    {
        ++linenum;
        current_line = trim(current_line);
        if (current_line.front() == '[' && current_line.back() == ']')
        {
            cur_field = current_line.substr(1, current_line.size() - 2);
            found_first_field = true;
            continue;
        }

        if (!found_first_field)
        {
            continue;
        }

        std::stringstream current_line_ss(current_line);
        std::string value;
        std::vector<std::string> values;
        while (std::getline(current_line_ss, value, '='))
        {
            values.push_back(trim(value));
        }
        // if format is not "a=b", pass
        if (values.size() != 2)
        {
            std::cout << "Warning : ignoring incorrect format in line :" << linenum << std::endl;
            continue;
        }

        manifest[cur_field][values[0]] = values[1];
    }

    if (!found_first_field)
        throw std::runtime_error("Incorrect manifest format: " + filename);

    return manifest;
}

void generate_manifest(const std::string &filename, const hdf_manifest &manifest)
{
    std::stringstream ss;
    for (const auto &[field, values] : manifest)
    {
        ss << "[" << field << "]" << std::endl;
        for (const auto &[key, fn] : values)
        {
            ss << key << "=" << fn << std::endl;
        }
    }
    std::ofstream ofile(filename, std::ios::out);
    ofile << ss.rdbuf();
}

bool store_hec_context_json(const std::string &filename, const heracles::data::FHEContext &context)
{
    std::string json_str;
    google::protobuf::util::JsonPrintOptions options;
    options.add_whitespace = true;
    options.always_print_primitive_fields = true;
    auto rc = ::google::protobuf::util::MessageToJsonString(context, &json_str, options);
    std::ofstream json_ofile(filename, std::ios::out);
    json_ofile << json_str;

    return true;
}

bool store_testvector_json(const std::string &filename, const heracles::data::TestVector &test_vector)
{
    std::string json_str;
    google::protobuf::util::JsonPrintOptions options;
    options.add_whitespace = true;
    options.always_print_primitive_fields = true;
    auto rc = ::google::protobuf::util::MessageToJsonString(test_vector, &json_str, options);
    std::ofstream json_ofile(filename, std::ios::out);

    json_ofile << json_str;
    return true;
}

void store_hec_context(
    hdf_manifest *manifest_out, const std::string &filename, const heracles::data::FHEContext &context_pb)
{
    auto tmp_context = context_pb;
    if (context_pb.ByteSizeLong() > (1 << 30))
    {
        int gkct = 1;
        for (const auto &[ge, key] : tmp_context.ckks_info().keys().rotation_keys())
        {
            std::stringstream parts_fnss;
            parts_fnss << filename << "_hec_context_part_" << gkct++;
            std::ofstream pb_ofile(parts_fnss.str(), std::ios::out | std::ios::binary);
            (*manifest_out)["rotation_keys"][std::to_string(ge)] = parts_fnss.str();
            if (!key.SerializeToOstream(&pb_ofile))
                throw std::runtime_error("Serializing rotation key failed");
        }
        tmp_context.mutable_ckks_info()->mutable_keys()->clear_rotation_keys();
    }

    auto main_fs = filename + "_hec_context_part_0";
    (*manifest_out)["context"]["main"] = main_fs;
    std::ofstream pb_ofile(main_fs, std::ios::out | std::ios::binary);
    if (!tmp_context.SerializeToOstream(&pb_ofile))
        throw std::runtime_error("Serializing main hec context failed");
}
void store_testvector(
    hdf_manifest *manifest_out, const std::string &filename, const heracles::data::TestVector &testvector_pb)
{
    if (testvector_pb.ByteSizeLong() > (1 << 30))
    {
        int tvct = 0;
        for (const auto &[sym, data_part] : testvector_pb.sym_data_map())
        {
            std::stringstream parts_fnss;
            parts_fnss << filename << "_testvector_part_" << tvct++;
            auto parts_fn = parts_fnss.str();
            (*manifest_out)["testvector"][sym] = parts_fn;
            std::ofstream pb_ofile(parts_fn, std::ios::out | std::ios::binary);
            if (!data_part.SerializeToOstream(&pb_ofile))
                throw std::runtime_error("Serializing test vector part " + sym + " failed. File : " + parts_fn);
        }
        return;
    }

    auto full_fn = filename + "_testvector_part_0";
    (*manifest_out)["testvector"]["full"] = full_fn;
    std::ofstream pb_ofile(full_fn, std::ios::out | std::ios::binary);
    if (!testvector_pb.SerializeToOstream(&pb_ofile))
        throw std::runtime_error("Serializing full test vector failed. File : " + full_fn);
}

bool store_data_trace(
    const std::string &filename, const heracles::data::FHEContext &context_pb,
    const heracles::data::TestVector &testvector_pb)
{
    hdf_manifest manifest_datatrace;
    try
    {
        store_hec_context(&manifest_datatrace, filename, context_pb);
        store_testvector(&manifest_datatrace, filename, testvector_pb);
        generate_manifest(filename, manifest_datatrace);
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during store_data_trace, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }

    return true;
}

void load_hec_context_from_manifest(heracles::data::FHEContext *context_pb, const hdf_manifest &manifest)
{
    try
    {
        std::filesystem::path main_fn(manifest.at("context").at("main"));
        std::ifstream context_pb_ifile(main_fn, std::ios::in | std::ios::binary);
        context_pb->ParseFromIstream(&context_pb_ifile);

        if (manifest.count("rotation_keys"))
        {
            for (const auto &[ge, gk_fn] : manifest.at("rotation_keys"))
            {
                heracles::data::KeySwitch gk_pb;
                std::ifstream gk_pb_ifile(gk_fn, std::ios::in | std::ios::binary);
                gk_pb.ParseFromIstream(&gk_pb_ifile);
                (*(context_pb->mutable_ckks_info()
                       ->mutable_keys()
                       ->mutable_rotation_keys()))[static_cast<std::uint32_t>(std::stoul(ge))] = gk_pb;
            }
        }
    }

    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during load_hec_context, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}
void load_testvector_from_manifest(heracles::data::TestVector *testvector_pb, const hdf_manifest &manifest)
{
    try
    {
        if (manifest.at("testvector").find("full") != manifest.at("testvector").end())
        { // single file
            const auto &full_fn = manifest.at("testvector").at("full");
            std::ifstream pb_ifile(full_fn, std::ios::in | std::ios::binary);
            testvector_pb->ParseFromIstream(&pb_ifile);
        }
        else
        { // segmented
            for (const auto &[sym, parts_fn] : manifest.at("testvector"))
            {
                std::ifstream pb_ifile(parts_fn, std::ios::in | std::ios::binary);
                (*testvector_pb->mutable_sym_data_map())[sym].ParseFromIstream(&pb_ifile);
            }
        }
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during _load_testvector, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }
}

heracles::data::FHEContext load_hec_context(const std::string &filename)
{
    heracles::data::FHEContext context_pb;
    try
    {
        auto manifest = parse_manifest(filename);
        load_hec_context_from_manifest(&context_pb, manifest);
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during load_data_trace, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }

    return context_pb;
}
heracles::data::TestVector load_testvector(const std::string &filename)
{
    heracles::data::TestVector testvector_pb;
    try
    {
        auto manifest = parse_manifest(filename);
        load_testvector_from_manifest(&testvector_pb, manifest);
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during load_data_trace, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }

    return testvector_pb;
}

std::pair<heracles::data::FHEContext, heracles::data::TestVector> load_data_trace(const std::string &filename)
{
    heracles::data::FHEContext context_pb;
    heracles::data::TestVector testvector_pb;
    try
    {
        auto manifest = parse_manifest(filename);
        load_hec_context_from_manifest(&context_pb, manifest);
        load_testvector_from_manifest(&testvector_pb, manifest);
    }
    catch (const std::runtime_error &err)
    {
        std::cerr << "Runtime error during load_data_trace, err: " << err.what() << std::endl;
        throw err;
    }
    catch (...)
    {
        std::cerr << "Unknown exception caught in " << __FUNCTION__ << "in file" << __FILE__ << std::endl;
        throw;
    }

    return { context_pb, testvector_pb };
}

} // namespace heracles::data
