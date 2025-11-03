// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#include "heracles/data/transform.h"
#include <algorithm>
#include <cassert>
#include <fstream>
#include <iostream>
#include <unordered_map>
#include <vector>
#include "heracles/data/math.h"
#include "heracles/util/util.h"

namespace hmath = heracles::math;
namespace hutildata = heracles::util::data;
namespace heracles::data
{
void extract_metadata_polys(
    heracles::data::MetadataPolynomials *metadata_polys, const heracles::data::FHEContext &context)
{
    auto sym_poly_map = metadata_polys->mutable_metadata()->mutable_sym_poly_map();

    auto N = context.n();
    std::uint32_t nQ = context.q_i_size();
    std::vector<uint32_t> psi(context.psi().begin(), context.psi().end());
    std::vector<uint32_t> psi_inv(psi.size());
    for (size_t i = 0; i < psi.size(); ++i)
        hmath::try_invert_uint_mod(psi[i], context.q_i(i), &psi_inv[i]); // 32

    std::set<uint32_t> galois_elts;
    if (context.scheme() == heracles::common::SCHEME_BGV)
    {
        for (const auto &pt : context.bgv_info().plaintext_specific())
        {
            auto keys = pt.keys();
            for (const auto &[ge, _] : keys.rotation_keys())
                galois_elts.insert(ge);
        }
    }
    else if (context.scheme() == heracles::common::SCHEME_CKKS)
    {
        for (const auto &[ge, _] : context.ckks_info().keys().rotation_keys())
            galois_elts.insert(ge);
    }

    for (std::uint32_t i = 0; i < nQ; ++i)
    {
        std::string key_psi_default = "psi_default_" + std::to_string(i);
        std::string key_ipsi_default = "ipsi_default_" + std::to_string(i);
        std::vector<uint32_t> vpsi(N), vipsi(N);
#pragma omp parallel for
        for (uint32_t j = 0; j < N; ++j)
        {
            vpsi[j] = hutildata::convert_to_montgomery(
                hmath::exponentiate_uint_mod(psi[i], j, context.q_i(i)), context.q_i(i));
            vipsi[j] = hutildata::convert_to_montgomery(
                hmath::exponentiate_uint_mod(psi_inv[i], j, context.q_i(i)), context.q_i(i));
        }
        hutildata::poly_bit_reverse(&(*sym_poly_map)[key_psi_default], vpsi);
        hutildata::poly_bit_reverse(&(*sym_poly_map)[key_ipsi_default], vipsi);

        // Get ql half and ql half mod q
        // Rescale: (qi-1) / 2 mod qj for all i < j, (i>=2)
        // mod_raise: (qi-1) / 2 mod qj for i=0,1 & all j
        if (context.scheme() == heracles::common::SCHEME_CKKS && i < context.q_size())
        {
            uint32_t qlHalf_i = context.q_i(i) >> 1;
            (*sym_poly_map)["qlHalf_" + hutildata::toStrKey({ i })].mutable_coeffs()->Resize(N, qlHalf_i);

            auto jMax = i <= 1 ? static_cast<int>(context.q_size()) : i;
            for (std::uint32_t j = 0; j < jMax; ++j)
            {
                (*sym_poly_map)["qlHalfModq_" + hutildata::toStrKey({ i, j })].mutable_coeffs()->Resize(
                    N, qlHalf_i % context.q_i(j));
            }
        }

        for (const uint32_t ge : galois_elts)
        {
            uint32_t exp_scale;
            hmath::try_invert_uint_mod(ge, 2 * N, &exp_scale); // 32
            std::string key_ipsi_ge_i = "ipsi_" + std::to_string(ge) + "_" + std::to_string(i);
            std::vector<uint32_t> tmp(N);
#pragma omp parallel for
            for (uint32_t j = 0; j < N; ++j)
            {
                tmp[j] = hutildata::convert_to_montgomery(
                    hmath::exponentiate_uint_mod(psi_inv[i], exp_scale * j, context.q_i(i)), context.q_i(i));
            }
            hutildata::poly_bit_reverse(&(*sym_poly_map)[key_ipsi_ge_i], tmp);
        }
    }

    // key switch keys
    if (context.scheme() == heracles::common::SCHEME_BGV)
    {
        for (int pt = 0; pt < context.bgv_info().plaintext_specific_size(); ++pt)
        {
            auto keys = context.bgv_info().plaintext_specific(pt).keys();
            std::string rlk_prefix = "rlk_" + std::to_string(pt);
            hutildata::transform_and_flatten_key_switch(
                metadata_polys->mutable_metadata(), rlk_prefix, keys.relin_key());
            for (const auto &[ge, key] : keys.rotation_keys())
            {
                std::stringstream gk_prefix;
                gk_prefix << "gk_" << pt << "_" << ge;
                hutildata::transform_and_flatten_key_switch(metadata_polys->mutable_metadata(), gk_prefix.str(), key);
            }
        }
    }
    else if (context.scheme() == heracles::common::SCHEME_CKKS)
    {
        auto keys = context.ckks_info().keys();
        std::string rlk_prefix = "rlk";
        hutildata::transform_and_flatten_key_switch(metadata_polys->mutable_metadata(), rlk_prefix, keys.relin_key());

        for (const auto &[ge, key] : keys.rotation_keys())
        {
            std::stringstream gk_prefix;
            gk_prefix << "gk_" << ge;
            hutildata::transform_and_flatten_key_switch(metadata_polys->mutable_metadata(), gk_prefix.str(), key);
        }
    }

    // bootstrapping
    if (context.scheme() == heracles::common::SCHEME_BGV)
    {
        if (context.bgv_info().has_recrypt_key())
            hutildata::transform_and_flatten_ciphertext(
                metadata_polys->mutable_metadata(), "bk", context.bgv_info().recrypt_key());
    }
    else if (context.scheme() == heracles::common::SCHEME_CKKS)
    {
        std::vector<uint32_t> zeros(N, 0);
        *((*sym_poly_map)["zero"].mutable_coeffs()) = { zeros.begin(), zeros.end() };
    }
}

void extract_metadata_twiddles(
    heracles::data::MetadataTwiddles *metadata_twiddles, const heracles::data::FHEContext &context)
{
    std::vector<uint32_t> omega;
    std::vector<uint32_t> omega_inv;
    omega.reserve(context.key_rns_num());
    omega_inv.reserve(context.key_rns_num());

    // TODO(skmono): replace "default" to "0" for future update on ntt/intt
    for (size_t i = 0; i < context.key_rns_num(); ++i)
    {
        omega.push_back(hmath::exponentiate_uint_mod(context.psi(i), 2U, context.q_i(i)));
        uint32_t inv;
        hmath::try_invert_uint_mod(omega.back(), context.q_i(i), &inv); // 32
        omega_inv.push_back(inv);
    }

    auto twiddles_ntt = metadata_twiddles->mutable_twiddles_ntt();
    auto twiddles_intt = metadata_twiddles->mutable_twiddles_intt();

    metadata_twiddles->set_only_power_of_two(false);

    for (size_t i = 0; i < context.key_rns_num(); ++i)
    {
        auto default_ntt = (*twiddles_ntt)["default"].add_rns_polys();
        auto default_intt = (*twiddles_intt)["default"].add_rns_polys();
        std::vector<uint32_t> vntt(context.n() / 2), vintt(context.n() / 2);
#pragma omp parallel for
        for (uint32_t j = 0; j < context.n() / 2; ++j)
        {
            vntt[j] = hutildata::convert_to_montgomery(
                hmath::exponentiate_uint_mod(omega[i], j, context.q_i(i)), context.q_i(i));
            vintt[j] = hutildata::convert_to_montgomery(
                hmath::exponentiate_uint_mod(omega_inv[i], j, context.q_i(i)), context.q_i(i));
        }
        *(default_ntt->mutable_coeffs()) = { vntt.begin(), vntt.end() };
        *(default_intt->mutable_coeffs()) = { vintt.begin(), vintt.end() };
        default_ntt->set_modulus(context.q_i(i));
        default_intt->set_modulus(context.q_i(i));
    }

    // twiddle factors for galois elements
    std::set<uint32_t> galois_elts;
    if (context.scheme() == heracles::common::SCHEME_BGV)
    {
        for (const auto &pt : context.bgv_info().plaintext_specific())
        {
            auto keys = pt.keys();
            for (const auto &[ge, _] : keys.rotation_keys())
                galois_elts.insert(ge);
        }
    }
    else if (context.scheme() == heracles::common::SCHEME_CKKS)
    {
        for (const auto &[ge, _] : context.ckks_info().keys().rotation_keys())
            galois_elts.insert(ge);
    }

    for (const uint32_t ge : galois_elts)
    {
        uint32_t exp_scale;
        hmath::try_invert_uint_mod(ge, 2 * context.n(), &exp_scale); // 32
        for (size_t i = 0; i < context.key_rns_num(); ++i)
        {
            auto ge_intt = (*twiddles_intt)[std::to_string(ge)].add_rns_polys();
            std::vector<uint32_t> vintt_ge(context.n() / 2);
#pragma omp parallel for
            for (uint32_t j = 0; j < context.n() / 2; ++j)
            {
                vintt_ge[j] = hutildata::convert_to_montgomery(
                    hmath::exponentiate_uint_mod(omega_inv[i], exp_scale * j, context.q_i(i)), context.q_i(i));
            }
            *(ge_intt->mutable_coeffs()) = { vintt_ge.begin(), vintt_ge.end() };
            ge_intt->set_modulus(context.q_i(i));
        }
    }
}

bool extract_metadata_immediates(
    heracles::data::MetadataImmediates *metadata_immediates, const heracles::data::FHEContext &context)
{
    auto sym_immediate_map = metadata_immediates->mutable_sym_immediate_map();
    (*sym_immediate_map)["one"] = 1;
    if (context.scheme() == heracles::common::SCHEME_BGV)
    {
        uint32_t inv = 0;

        for (size_t i = 0; i < context.key_rns_num(); ++i)
        {
            (*sym_immediate_map)["R2_" + std::to_string(i)] =
                hmath::exponentiate_uint_mod(hutildata::montgomery_R, 2UL, static_cast<uint64_t>(context.q_i(i)));
            hmath::try_invert_uint_mod(context.n(), context.q_i(i), &inv); // 32
            (*sym_immediate_map)["iN_" + std::to_string(i)] = hutildata::convert_to_montgomery(inv, context.q_i(i));
            for (size_t j = 0; j < i; ++j)
            {
                hmath::try_invert_uint_mod(context.q_i(i), context.q_i(j), &inv); // 32
                (*sym_immediate_map)["inv_q_i_" + std::to_string(i) + "_mod_q_j_" + std::to_string(j)] =
                    hutildata::convert_to_montgomery(inv, context.q_i(j));
            }
            for (int pt = 0; pt < context.bgv_info().plaintext_specific_size(); ++pt)
            {
                hmath::try_invert_uint_mod(
                    static_cast<uint32_t>(context.bgv_info().plaintext_specific(pt).plaintext_modulus()),
                    context.q_i(i), &inv); // 32
                (*sym_immediate_map)["neg_inv_t_" + std::to_string(pt) + "_mod_q_i_" + std::to_string(i)] =
                    hutildata::convert_to_montgomery(-inv, context.q_i(i));
                (*sym_immediate_map)["t_" + std::to_string(pt) + "_mod_q_i_" + std::to_string(i)] =
                    hutildata::convert_to_montgomery(
                        context.bgv_info().plaintext_specific(pt).plaintext_modulus(), context.q_i(i));
            }
        }

        (*sym_immediate_map)["iN"] = static_cast<uint32_t>(0x100000000ULL / static_cast<uint64_t>(context.n()));
        auto k = context.bgv_info().plaintext_specific(0).keys().relin_key().k();
        uint32_t p = context.q_i(context.key_rns_num() - 1);
        for (uint32_t i = 0; i < context.key_rns_num() - 1; ++i)
        {
            hmath::try_invert_uint_mod(p, context.q_i(i), &inv); // 32
            (*sym_immediate_map)["inv_p_mod_q_i_" + std::to_string(i)] =
                hutildata::convert_to_montgomery(inv, context.q_i(i));
        }

        for (size_t l = 0; l < context.key_rns_num() - 1; ++l)
        {
            for (size_t j = 0; j < context.key_rns_num(); ++j)
            {
                for (uint32_t i = 0; i < l + 1; ++i)
                {
                    uint32_t q_over_qi_mod_qj = 1;
                    for (size_t k = 0; k < context.key_rns_num(); ++k)
                    {
                        if (k != i)
                            q_over_qi_mod_qj =
                                hmath::multiply_uint_mod(q_over_qi_mod_qj, context.q_i(k), context.q_i(j)); // 32
                    }
                    (*sym_immediate_map)
                        ["base_change_matrix_" + std::to_string(i) + "_" + std::to_string(j) + "_" +
                         std::to_string(k)] = hutildata::convert_to_montgomery(q_over_qi_mod_qj, context.q_i(j));
                    if (i == j)
                    {
                        hmath::try_invert_uint_mod(q_over_qi_mod_qj, context.q_i(i), &inv); // 32
                        (*sym_immediate_map)["inv_punctured_prod_" + std::to_string(i) + "_" + std::to_string(i)] =
                            hutildata::convert_to_montgomery(inv, context.q_i(i));
                    }
                }
            }
        }
    }
    else if (context.scheme() == heracles::common::SCHEME_CKKS)
    {
        uint32_t inv = 0;

        auto dnum = context.digit_size();
        auto alpha = context.alpha();
        auto sizeQ = context.q_size();
        auto sizeP = context.key_rns_num() - sizeQ;

        for (size_t i = 0; i < context.key_rns_num(); ++i)
        {
            (*sym_immediate_map)["R2_" + std::to_string(i)] =
                hmath::exponentiate_uint_mod(hutildata::montgomery_R, 2UL, static_cast<uint64_t>(context.q_i(i)));
            hmath::try_invert_uint_mod(context.n(), context.q_i(i), &inv); // 32
            (*sym_immediate_map)["iN_" + std::to_string(i)] = hutildata::convert_to_montgomery(inv, context.q_i(i));
        }
        (*sym_immediate_map)["iN"] = static_cast<uint32_t>(0x100000000ULL / static_cast<uint64_t>(context.n()));

        // TODO: remove dnum/alpha
        // Get q0 inv mod q1 and  q1 inv mod q0 for ModRaise kernel
        std::uint32_t q0InvModq1 = heracles::math::get_invert_uint_mod(context.q_i(0), context.q_i(1));
        std::uint32_t q1InvModq0 = heracles::math::get_invert_uint_mod(context.q_i(1), context.q_i(0));
        (*sym_immediate_map)["q0InvModq1"] = hutildata::convert_to_montgomery(q0InvModq1, context.q_i(1));

        (*sym_immediate_map)["q1InvModq0"] = hutildata::convert_to_montgomery(q1InvModq0, context.q_i(0));

        // Metadata for key-switching (Relin, Rotate)
        // PartQHatInvModq_{i}_{j} = (Q/Qi)^-1 mod qj; equals to zero for qj \notin Qi
        for (uint32_t i = 0; i < dnum; ++i)
        {
            for (uint32_t j = 0; j < sizeQ; ++j)
            {
                (*sym_immediate_map)["partQHatInvModq_" + hutildata::toStrKey({ i, j })] =
                    hutildata::convert_to_montgomery(
                        context.ckks_info().metadata_extra().at("partQHatInvModq_" + hutildata::toStrKey({ i, j })),
                        context.q_i(j));
            }
        }

        // PartQlHatInvModq_{i}_{j}_{l} = (Q^(i*alpha + j)_i/ql)^-1 mod ql for ql \in Q^(i*alpha + j)_i
        for (uint32_t i = 0; i < dnum; ++i)
        {
            uint32_t digitSize = i < (dnum - 1) ? alpha : sizeQ - alpha * (dnum - 1);
            for (uint32_t j = 0; j < digitSize; ++j)
            {
                for (uint32_t l = 0; l < j + 1; ++l)
                {
                    (*sym_immediate_map)["partQlHatInvModq_" + hutildata::toStrKey({ i, j, l })] =
                        hutildata::convert_to_montgomery(
                            context.ckks_info().metadata_extra().at(
                                "partQlHatInvModq_" + hutildata::toStrKey({ i, j, l })),
                            context.q_i(alpha * i + l));
                }
            }
        }

        // PartQlHatModp_{i}_{j}_{l}_{s} = (Q^(i)_j/ql)^-1 mod qs or ps, for qs \notin Q^(i)_j
        for (uint32_t i = 0; i < sizeQ; ++i)
        {
            uint32_t beta = std::ceil(static_cast<float>(i + 1) / static_cast<float>(alpha));
            for (uint32_t j = 0; j < beta; ++j)
            {
                uint32_t digitSize = j < beta - 1 ? alpha : (i + 1) - alpha * (beta - 1);
                auto sizeCompl = (i + 1) + sizeP - digitSize;
                for (uint32_t l = 0; l < digitSize; ++l)
                {
                    for (uint32_t s = 0; s < sizeCompl; ++s)
                    {
                        size_t idx =
                            s < alpha * j ? s : (s < i + 1 - digitSize ? s + digitSize : s + digitSize + sizeQ - i - 1);
                        (*sym_immediate_map)["partQlHatModp_" + hutildata::toStrKey({ i, j, l, s })] =
                            hutildata::convert_to_montgomery(
                                context.ckks_info().metadata_extra().at(
                                    "partQlHatModp_" + hutildata::toStrKey({ i, j, l, s })),
                                context.q_i(idx));
                    }
                }
            }
        }

        // pInvModq_{i} = P^{-1} mod qi
        for (uint32_t i = 0; i < sizeQ; ++i)
        {
            (*sym_immediate_map)["pInvModq_" + std::to_string(i)] = hutildata::convert_to_montgomery(
                context.ckks_info().metadata_extra().at("pInvModq_" + std::to_string(i)), context.q_i(i));
            (*sym_immediate_map)["pModq_" + std::to_string(i)] = hutildata::convert_to_montgomery(
                context.ckks_info().metadata_extra().at("pModq_" + std::to_string(i)), context.q_i(i));
        }

        // pInvModp_{i} = P^{-1} mod pi
        for (uint32_t i = 0; i < sizeP; ++i)
            (*sym_immediate_map)["pHatInvModp_" + std::to_string(i)] = hutildata::convert_to_montgomery(
                context.ckks_info().metadata_extra().at("pHatInvModp_" + std::to_string(i)), context.q_i(i + sizeQ));

        // pHatModq_{i}_{j} = P/pi mod qj
        for (uint32_t i = 0; i < sizeP; ++i)
        {
            for (uint32_t j = 0; j < sizeQ; ++j)
            {
                (*sym_immediate_map)["pHatModq_" + hutildata::toStrKey({ i, j })] = hutildata::convert_to_montgomery(
                    context.ckks_info().metadata_extra().at("pHatModq_" + hutildata::toStrKey({ i, j })),
                    context.q_i(j));
            }
        }

        // Metadata for Rescale
        // qlInvModq_{i}_{j} = q_{sizeQ-(i+1)}^{-1} mod qj
        // QlQlInvModqlDivqlModq_{i}_{j} = ((Q/q_{sizeQ-(i+1)})^{-1} mod q_{sizeQ-(i+1)} * (Q/q_{sizeQ-(i+1)})) mod
        // qj
        for (uint32_t i = 0; i < sizeQ - 1; ++i)
        {
            for (uint32_t j = 0; j < sizeQ - i - 1; ++j)
            {
                (*sym_immediate_map)["qlInvModq_" + hutildata::toStrKey({ i, j })] = hutildata::convert_to_montgomery(
                    context.ckks_info().metadata_extra().at("qlInvModq_" + hutildata::toStrKey({ i, j })),
                    context.q_i(j));
                (*sym_immediate_map)["QlQlInvModqlDivqlModq_" + hutildata::toStrKey({ i, j })] =
                    hutildata::convert_to_montgomery(
                        context.ckks_info().metadata_extra().at(
                            "QlQlInvModqlDivqlModq_" + hutildata::toStrKey({ i, j })),
                        context.q_i(j));
            }
        }

        // Metadata for Bootstrap
        for (size_t i = 0; i < 2; ++i)
        {
            for (size_t j = 0; j < sizeQ; ++j)
            {
                (*sym_immediate_map)["qlModq_" + std::to_string(i) + "_" + std::to_string(j)] =
                    hutildata::convert_to_montgomery(context.q_i(i), context.q_i(j));
            }
        }

        auto boot_correction = context.ckks_info().metadata_extra().at("boot_correction");
        for (std::uint32_t i = 0; i < 32; ++i)
        {
            std::uint32_t val = 1 << i;
            for (size_t j = 0; j < sizeQ; ++j)
            {
                (*sym_immediate_map)["bmu_" + std::to_string(val) + "_" + std::to_string(j)] =
                    hutildata::convert_to_montgomery(val, context.q_i(j));
                // only perform once
                if (i == 0)
                    (*sym_immediate_map)["bmu_" + std::to_string(boot_correction)] =
                        hutildata::convert_to_montgomery(boot_correction, context.q_i(j));
            }
        }
    }
    else
        return false;

    return true;
}

void extract_polys(heracles::data::DataPolynomials *polys, const heracles::data::TestVector &testvector)
{
    for (const auto &[key, data] : testvector.sym_data_map())
    {
        hutildata::transform_and_flatten_dcrtpoly(polys->mutable_data(), key, data.dcrtpoly());
    }
}

void extract_metadata_params(heracles::data::MetadataParams *metadata_params, const heracles::data::FHEContext &context)
{
    auto sym_param_map = metadata_params->mutable_sym_param_map();
    (*sym_param_map)["key_rns_num"] = context.key_rns_num();
    (*sym_param_map)["digit_size"] = context.digit_size();
    (*sym_param_map)["q_size"] = context.q_size();
    (*sym_param_map)["alpha"] = context.alpha();

    // TODO: this is duplicate of above "digit_size", later merge two one
    (*sym_param_map)["dnum"] = context.digit_size();
}

void convert_polys_to_testvector(heracles::data::TestVector *testvector, const heracles::data::DataPolynomials &polys)
{
    std::unordered_map<std::string, std::pair<uint32_t, uint32_t>> sym_map;
    for (const auto &item : polys.data().sym_poly_map())
    {
        // find root symbol and order/num_rns
        auto [sym_basename, order, rns] = hutildata::split_symbol_name(item.first);
        if (sym_map.find(sym_basename) == sym_map.end())
        {
            sym_map[sym_basename] = { order + 1, rns + 1 };
            continue;
        }
        auto &[order_max, rns_num] = sym_map[sym_basename];
        order_max = std::max(order_max, order + 1);
        rns_num = std::max(rns_num, rns + 1);
    }

    auto merge_sym = [](std::string root, uint32_t o, uint32_t r) {
        return root + "_" + std::to_string(o) + "_" + std::to_string(r);
    };

    for (const auto &[sym_basename, params] : sym_map)
    {
        heracles::data::DCRTPoly data;
        for (uint32_t i = 0; i < params.first; ++i)
        {
            auto poly = data.add_polys();
            for (uint32_t j = 0; j < params.second; ++j)
            {
                hutildata::convert_rnspoly_to_original(
                    poly->add_rns_polys(), polys.data().sym_poly_map().at(merge_sym(sym_basename, i, j)));
            }
        }
        *((*(testvector->mutable_sym_data_map()))[sym_basename].mutable_dcrtpoly()) = data;
    }
}

void prune_polys(
    heracles::data::TestVector *testvector, const heracles::data::FHEContext &context,
    const heracles::fhe_trace::Trace &trace)
{
    throw std::logic_error("Not yet implemented!");
}

} // namespace heracles::data
