// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "heracles/heracles_proto.h"

namespace heracles::data
{
// Note: extraction does all expansion and transformation, e.g., bit-reversal and montgomery conversion of
// data in context & test-vectors. I.e., test-vector and context are mostly HEC agnostic ...

/*
        Extract symbol/value map of all metadata polynomials as needed to build (after swizzling) memory images or
   DMA downloads
    */
void extract_metadata_polys(
    heracles::data::MetadataPolynomials *metadata_polys, const heracles::data::FHEContext &context);

/*
        Extract symbol/value map of all twiddles as needed to build (after swizzling & replicating) memory images or
   DMA downloads
    */
void extract_metadata_twiddles(
    heracles::data::MetadataTwiddles *metadata_twiddles, const heracles::data::FHEContext &context);

/*
        Extract symbol/value map of all immediates as needed for final code instantiation
    */
bool extract_metadata_immediates(
    heracles::data::MetadataImmediates *metadata_immediates, const heracles::data::FHEContext &context);

/*
        Extract symbol/value map of all input/output polynomials as needed to build (after swizzling) memory images
   or DMA downloads
    */
void extract_polys(heracles::data::DataPolynomials *polys, const heracles::data::TestVector &testvector);

/*
        Extract metadata parameters (no polynomials, immediates and twiddles) - downsized context
    */
void extract_metadata_params(
    heracles::data::MetadataParams *metadata_params, const heracles::data::FHEContext &context);

void convert_polys_to_testvector(heracles::data::TestVector *testvector, const heracles::data::DataPolynomials &polys);

/*
        Prune data polynomials based on trace - unused data are removed
    */
void prune_polys(
    heracles::data::TestVector *testvector, const heracles::data::FHEContext &context,
    const heracles::fhe_trace::Trace &trace);

} // namespace heracles::data
