// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include "poly_description.h"

using namespace pisa::poly;

namespace pisa::poly::library::core {
/** \brief PolyOperation addition PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Add("add", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation subtraction PolyOperationDesc
 *   Op name: add
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | specifies the FHE_SCHEME of the poly operation |
 * */
static const PolyOperationDesc Sub("sub", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation multiplication PolyOperationDesc
 *   Op name: add
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | specifies the FHE_SCHEME of the poly operation |
 * */
static const PolyOperationDesc Mul("mul", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation Square PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 * */
static const PolyOperationDesc Square("square", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation Relin PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Relin("relin", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, ALPHA, QSIZE, DNUM });

/** \brief PolyOperation ModSwitch PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc ModSwitch("mod", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation Ntt PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Ntt("ntt", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation Intt PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Intt("intt", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT });

/** \brief PolyOperation Rescale PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Rescale("rescale", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, QSIZE });

/** \brief PolyOperation Rotate PolyOperationDesc
 *   Adds two polynomials with specified specified polymodulus degree, RNS terms, and polynomial parts and writes the result to the specified output.
 *  | Param | description |
 *  | ----- | ----------- |
 *  | FHE_SCHEME   | Not Used |
 *  | POLYMOD_DEG_LOG2   | Specifies the modulus degree of the input polynomials |
 *  | KEY_RNS   | Specifies number of RNS key values. Not Used |
 *  | RNS_TERM   | specifies the number of RNS terms of the input polynomials |
 *  | CIPHER_DEGREE   | Specifies the number of polynomial parts |
 *  | OP_NAME   | add |
 *  | OUTPUT_ARGUMENT   | Destination ciphertext |
 *  | INPUT_ARGUMENT   | Input1 ciphertext label |
 *  | INPUT_ARGUMENT   | Input2 ciphertext label |
 * */
static const PolyOperationDesc Rotate("rotate", { OP_NAME, FHE_SCHEME, POLYMOD_DEG_LOG2, KEY_RNS, OUTPUT_ARGUMENT, INPUT_ARGUMENT, GALOIS_ELT, ALPHA, QSIZE, DNUM });
} // namespace pisa::poly::library::core
