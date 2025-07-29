# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# Note: see also the C++ definition of equivalent functions
# - given that some of these function might evolve, best done via shared code & native code integration in python
# TODO: Duplicate in C++ and revert below into native code invocations ..

import functools as ft
import math
import operator as op

import heracles.proto.common_pb2 as hpc
import heracles.proto.data_pb2 as hpd
import heracles.util.data as hud


def galois_elements_from_context(context: hpd.FHEContext) -> set:
    match context.scheme:
        case hpc.SCHEME_BGV:
            return {ge for pt in context.bgv_info.plaintext_specific for ge, _ in pt.keys.rotation_keys.items()}
        case hpc.SCHEME_CKKS:
            return set(context.ckks_info.keys.rotation_keys.keys())
        case _:
            raise ValueError("Only BGV and CKKS schemes are supported.")


def extract_metadata_polys(context: hpd.FHEContext) -> hpd.MetadataPolynomials:
    """
    Extract symbol/value map of all metadata polynomials as needed to build (after swizzling) memory images or DMA downloads
    """
    N = context.N
    q_i = context.q_i
    nQ = len(q_i)
    psi = context.psi
    psi_inv = [pow(psi, -1, q) for psi, q in zip(context.psi, q_i, strict=False)]
    # UNUSED? k = context.ckks_info.keys.relin_key.k
    #         if context.scheme == hpc.SCHEME_CKKS else context.bgv_info.plaintext_specific[0].keys.relin_key.k

    meta_polys = hpd.MetadataPolynomials()

    # - galois_element-specific version for rotation
    galois_elts = galois_elements_from_context(context)
    for i in range(nQ):
        # TODO (eventually): refactor below to common naming functions

        # - powers of psi for negative wrapped convolusion
        #   - default version for ntt, mod-switch & relin
        meta_polys.metadata.sym_poly_map[f"psi_default_{i}"].coeffs.extend(
            hud.convert_to_montgomery(pow(psi[i], j, q_i[i]), q_i[i]) for j in range(N)
        )
        hud.poly_bit_reverse_inplace(meta_polys.metadata.sym_poly_map[f"psi_default_{i}"])

        meta_polys.metadata.sym_poly_map[f"ipsi_default_{i}"].coeffs.extend(
            hud.convert_to_montgomery(pow(psi_inv[i], j, q_i[i]), q_i[i]) for j in range(N)
        )
        hud.poly_bit_reverse_inplace(meta_polys.metadata.sym_poly_map[f"ipsi_default_{i}"])

        # calculate in house
        if context.scheme == hpc.SCHEME_CKKS and i < context.q_size:
            # TODO: Revisit later if addi/subi is added, then we can put these to meta_immediates, instead of meta_polys
            # ql_half
            # for i in range(context.q_size):
            qlHalf_i = q_i[i] >> 1
            meta_polys.metadata.sym_poly_map[f"qlHalf_{i}"].coeffs.extend([qlHalf_i] * N)

            jMax = context.q_size if i <= 1 else i
            # ql_half_modq
            #  Rescale: (qi-1) / 2 mod qj for all i < j, (i>=2)
            # mod_raise: (qi-1) / 2 mod qj for i=0,1 & all j
            for j in range(jMax):
                meta_polys.metadata.sym_poly_map[f"qlHalfModq_{i}_{j}"].coeffs.extend([qlHalf_i % q_i[j]] * N)

        for ge in galois_elts:
            exp_scale = pow(ge, -1, 2 * N)
            # if i >= nQ - k:
            #     # the ones for the special primes have to be the normal, not the rotation ones
            #     # NOTE: boot_apply_galois also does use these ipsi/psi but as computed in
            #     #    SEAL-Bootstrapping implies all-rotation variants, so would fail psim/simics
            #     #    comparison when run with polynomials of key_nrns terms.  Luckily, that is not
            #     #    a needed scenario, so re-using these is fine (but to be safe, we do check also
            #     #    during the mappings)
            #     exp_scale = 1
            # else:
            #     exp_scale = inv_ge
            meta_polys.metadata.sym_poly_map[f"ipsi_{str(ge)}_{i}"].coeffs.extend(
                hud.convert_to_montgomery(pow(psi_inv[i], exp_scale * j, q_i[i]), q_i[i]) for j in range(N)
            )
            hud.poly_bit_reverse_inplace(meta_polys.metadata.sym_poly_map[f"ipsi_{str(ge)}_{i}"])
            # NOTE: we need only rotation-specific intt twiddles, not ntt ones but to keep logic in psim & step1
            #   simple and uniform, we still create a separate version
            # meta_polys.metadata.sym_poly_map[f"psi_{str(ge)}_{i}"].coeffs.extend(
            #      [hud.convert_to_montgomery(pow(psi[i], j, q_i[i]), q_i[i]) for j in range(N)])
            # hud.poly_bit_reverse_inplace(meta_polys.metadata.sym_poly_map[f"psi_{str(ge)}_{i}"])

    # - key-switch keys
    if context.scheme == hpc.SCHEME_BGV:
        for pt in context.bgv_info.plaintext_specific:
            # - relin
            transform_and_flatten_key_switch(
                context,
                f"rlk_{pt}",
                pt.keys.relin_key,
                meta_polys.metadata.sym_poly_map,
            )
            # - rotation
            for ge, rk in pt.keys.rotation_keys.items():
                transform_and_flatten_key_switch(
                    context,
                    f"gk_{pt}_{ge}",
                    rk,
                    meta_polys.metadata.sym_poly_map,
                )
    elif context.scheme == hpc.SCHEME_CKKS:
        keys = context.ckks_info.keys
        # - relin
        transform_and_flatten_key_switch(context, "rlk", keys.relin_key, meta_polys.metadata.sym_poly_map)
        # - rotation
        for ge, rk in keys.rotation_keys.items():
            transform_and_flatten_key_switch(
                context,
                f"gk_{ge}",
                rk,
                meta_polys.metadata.sym_poly_map,
            )

    # for bootstrapping
    if context.scheme == hpc.SCHEME_BGV and context.bgv_info.recrypt_key:
        transform_and_flatten_ciphertext(
            context,
            "bk",
            context.bgv_info.recrypt_key,
            meta_polys.metadata.sym_poly_map,
        )
    elif context.scheme == hpc.SCHEME_CKKS:
        # zero polys added
        meta_polys.metadata.sym_poly_map["zero"].coeffs.extend([0] * N)

    return meta_polys


def extract_metadata_twiddles(context: hpd.FHEContext) -> hpd.MetadataTwiddles:
    """
    Extract symbol/value map of all twiddles as needed to build (after swizzling & replicating) memory images or DMA downloads
    """
    N = context.N
    q_i = context.q_i
    nQ = len(q_i)
    # UNUSED? psi = context.psi
    omega = [pow(psi, 2, q) for psi, q in zip(context.psi, q_i, strict=False)]
    omega_inv = [pow(o, -1, q) for o, q in zip(omega, q_i, strict=False)]
    # UNUSED? k = context.ckks_info.keys.relin_key.k
    #         if context.scheme == hpc.SCHEME_CKKS else context.bgv_info.plaintext_specific[0].keys.relin_key.k

    twiddles = hpd.MetadataTwiddles()
    twiddles.only_power_of_two = False
    # "normal" twiddles
    for i in range(nQ):
        twiddles.twiddles_ntt["default"].rns_polys.add().coeffs.extend(
            hud.convert_to_montgomery(pow(omega[i], j, q_i[i]), q_i[i]) for j in range(N // 2)
        )
        twiddles.twiddles_intt["default"].rns_polys.add().coeffs.extend(
            hud.convert_to_montgomery(pow(omega_inv[i], j, q_i[i]), q_i[i]) for j in range(N // 2)
        )
    # rotation related twiddles
    galois_elts = galois_elements_from_context(context)
    for ge in galois_elts:
        exp_scale = pow(ge, -1, 2 * N)
        for i in range(nQ):
            # inv_ge = pow(ge, -1, 2 * N)
            # if i >= nQ - k:
            #     # the ones for the special primes have to be the normal, not the rotation ones
            #     # (see also additional comments in extract_metadata_polys regarding these psi/ipsis)
            #     exp_scale = 1
            # else:
            #     exp_scale = inv_ge
            twiddles.twiddles_intt[str(ge)].rns_polys.add().coeffs.extend(
                hud.convert_to_montgomery(pow(omega_inv[i], exp_scale * j, q_i[i]), q_i[i]) for j in range(N // 2)
            )
            # NOTE we need only rotation-specific intt twiddles, not ntt ones but to keep logic in psim & step1
            #   simple and uniform, we still create a separate version
            # twiddles.twiddles_ntt[str(ge)].rns_polys.add().coeffs.extend(
            #      [hud.convert_to_montgomery(pow(omega[i], j, q_i[i]), q_i[i]) for j in range(N//2)])

    return twiddles


def extract_metadata_immediates(context: hpd.FHEContext) -> hpd.MetadataImmediates:  # noqa: C901
    """
    Extract symbol/value map of all immediates as needed for final code instantiation
    """
    N = context.N
    q_i = context.q_i
    nQ = context.key_rns_num  # is same with len(q_i)

    immediates = hpd.MetadataImmediates()
    # NOTE: the "real" 1, not montgomery 1 !!
    immediates.sym_immediate_map["one"] = 1

    if context.scheme == hpc.SCHEME_CKKS:
        # dnum = # of digits
        dnum = context.digit_size
        # alpha = ceil(sizeQ / dnum); # of RNS primes in each digit
        alpha = context.alpha
        # sizeQ = nQ - sizeP
        sizeQ = context.q_size
        sizeP = nQ - sizeQ

        for i, q in enumerate(q_i):
            immediates.sym_immediate_map[f"R2_{i}"] = hud.montgomery_R**2 % q
            immediates.sym_immediate_map[f"iN_{i}"] = hud.convert_to_montgomery(pow(N, -1, q), q)

        # Global Metadata
        # iN, the inverse of N mod q_i but is identical in montgomery form across moduli but as we use
        # iN_i in some cases (e.g., in some psim scripts) and iN in others we generate both
        immediates.sym_immediate_map.update(
            {
                "iN": (1 << 32) // N,
                "q0InvModq1": hud.convert_to_montgomery(pow(q_i[0], -1, q_i[1]), q_i[1]),
                "q1InvModq0": hud.convert_to_montgomery(pow(q_i[1], -1, q_i[0]), q_i[0]),
            }
        )

        # Metadata for key-switching (Relin, Rotate)
        # PartQHatInvModq_{i}_{j} = (Q/Qi)^-1 mod qj; equals to zero for qj \notin Qi
        for i in range(dnum):
            for j in range(sizeQ):
                immediates.sym_immediate_map[f"partQHatInvModq_{i}_{j}"] = hud.convert_to_montgomery(
                    context.ckks_info.metadata_extra[f"partQHatInvModq_{i}_{j}"],
                    q_i[j],
                )
        # PartQlHatInvModq_{i}_{j}_{l} = (Q^(i*alpha + j)_i/ql)^-1 mod ql for ql \in Q^(i*alpha + j)_i
        for i in range(dnum):
            digitSize = alpha if i < dnum - 1 else sizeQ - alpha * (dnum - 1)
            for j in range(digitSize):
                for l in range(j + 1):  # noqa E741
                    immediates.sym_immediate_map[f"partQlHatInvModq_{i}_{j}_{l}"] = hud.convert_to_montgomery(
                        context.ckks_info.metadata_extra[f"partQlHatInvModq_{i}_{j}_{l}"],
                        q_i[alpha * i + l],
                    )
        # PartQlHatModp_{i}_{j}_{l}_{s} = (Q^(i)_j/ql)^-1 mod qs or ps, for qs \notin Q^(i)_j
        for i in range(sizeQ):
            beta = math.ceil(float(i + 1) / alpha)
            for j in range(beta):
                digitSize = alpha if j < beta - 1 else (i + 1) - alpha * (beta - 1)
                sizeCompl = (i + 1) - digitSize + sizeP
                for l in range(digitSize):  # noqa E741
                    for s in range(sizeCompl):
                        if s < alpha * j:
                            idx = s
                        elif s < (i + 1) - digitSize:
                            idx = s + digitSize
                        else:
                            idx = s - (i + 1) + digitSize + sizeQ
                        immediates.sym_immediate_map[f"partQlHatModp_{i}_{j}_{l}_{s}"] = hud.convert_to_montgomery(
                            context.ckks_info.metadata_extra[f"partQlHatModp_{i}_{j}_{l}_{s}"],
                            q_i[idx],
                        )

        # pInvModq_{i} = P^{-1} mod qi
        for i in range(sizeQ):
            immediates.sym_immediate_map[f"pInvModq_{i}"] = hud.convert_to_montgomery(
                context.ckks_info.metadata_extra[f"pInvModq_{i}"], q_i[i]
            )
            immediates.sym_immediate_map[f"pModq_{i}"] = hud.convert_to_montgomery(context.ckks_info.metadata_extra[f"pModq_{i}"], q_i[i])
        # pInvModp_{i} = P^{-1} mod pi
        for i in range(sizeP):
            idx = i + sizeQ
            immediates.sym_immediate_map[f"pHatInvModp_{i}"] = hud.convert_to_montgomery(
                context.ckks_info.metadata_extra[f"pHatInvModp_{i}"], q_i[idx]
            )
        # pHatModq_{i}_{j} = P/pi mod qj
        for i in range(sizeP):
            for j in range(sizeQ):
                immediates.sym_immediate_map[f"pHatModq_{i}_{j}"] = hud.convert_to_montgomery(
                    context.ckks_info.metadata_extra[f"pHatModq_{i}_{j}"], q_i[j]
                )

        # Metadata for Rescale
        # qlInvModq_{i}_{j} = q_{sizeQ-(i+1)}^{-1} mod qj
        for i in range(sizeQ - 1):
            for j in range(sizeQ - (i + 1)):
                immediates.sym_immediate_map[f"qlInvModq_{i}_{j}"] = hud.convert_to_montgomery(
                    context.ckks_info.metadata_extra[f"qlInvModq_{i}_{j}"], q_i[j]
                )
                # QlQlInvModqlDivqlModq_{i}_{j} = ((Q/q_{sizeQ-(i+1)})^{-1} mod q_{sizeQ-(i+1)} * (Q/q_{sizeQ-(i+1)})) mod qj
                immediates.sym_immediate_map[f"QlQlInvModqlDivqlModq_{i}_{j}"] = hud.convert_to_montgomery(
                    context.ckks_info.metadata_extra[f"QlQlInvModqlDivqlModq_{i}_{j}"],
                    q_i[j],
                )

        # Metadata for Bootstrap
        for i in (0, 1):
            for j in range(sizeQ):
                immediates.sym_immediate_map[f"qlModq_{i}_{j}"] = hud.convert_to_montgomery(context.q_i[i], q_i[j])

        # Metadata for boot_mul_uint
        for i in range(32):
            val = 1 << i
            for j in range(sizeQ):
                immediates.sym_immediate_map[f"bmu_{val}_{j}"] = hud.convert_to_montgomery(val, q_i[j])
                if i == 0:
                    boot_correction = context.ckks_info.metadata_extra["boot_correction"]
                    immediates.sym_immediate_map[f"bmu_{boot_correction}_{j}"] = hud.convert_to_montgomery(boot_correction, q_i[j])

    else:  # SCHEME_BGV
        for i, q in enumerate(q_i):
            immediates.sym_immediate_map[f"R2_{i}"] = hud.montgomery_R**2 % q
            immediates.sym_immediate_map[f"iN_{i}"] = hud.convert_to_montgomery(pow(N, -1, q), q)
            for j in range(i):
                immediates.sym_immediate_map[f"inv_q_i_{i}_mod_q_j_{j}"] = hud.convert_to_montgomery(pow(q, -1, q_i[j]), q_i[j])
            if context.scheme == hpc.SCHEME_BGV:
                bgv_info = context.bgv_info
                for pt_idx, pt in enumerate(bgv_info.plaintext_specific):
                    immediates.sym_immediate_map[f"neg_inv_t_{pt}_mod_q_i_{i}"] = hud.convert_to_montgomery(
                        -pow(pt.plaintext_modulus, -1, q), q
                    )
                    immediates.sym_immediate_map[f"t_{pt_idx}_mod_q_i_{i}"] = hud.convert_to_montgomery(pt.plaintext_modulus, q)

        immediates.sym_immediate_map["iN"] = (1 << 32) // N
        # iN, the inverse of N mod q_i but is identical in montgomery form across moduli but as we use
        # iN_i in some cases (e.g., in some psim scripts) and iN in others we generate both

        k = (
            context.ckks_info.keys.relin_key.k
            if context.scheme == hpc.SCHEME_CKKS
            else context.bgv_info.plaintext_specific[0].keys.relin_key.k
        )
        # NOTE we assume _all_ keys have same digit size!!
        p = ft.reduce(op.mul, [q_i[context.key_rns_num - i - 1] for i in range(k)])
        for i in range(nQ - k):
            immediates.sym_immediate_map[f"inv_p_mod_q_i_{i}"] = hud.convert_to_montgomery(pow(p, -1, q_i[i]), q_i[i])

        # for base-extension in bootstrapping, boot_dot_prod kernel needs
        # - base_change_matrix[i][l+j] := q/q_i mod q_{l+j} for 0 <= i <= l and 1 <= j <= L-l
        # - inv_punctured_prod[i] = (q/q_i)^{-1} mod q_i for 0 <= i <= l
        # with l number of rns of input and L the number of rns terms of a key
        # and q = product_i=0..l(q_i) / Q = product_i=0..L(q_i)
        # Then, from RNS_q(a), we can compute RNS_Q(a+qI) via (sum_{0 <= i <= l} base_change_matrix[i][j] *
        # (inv_punctured_prod[i] * a mod q_i)) mod q_{l+j} for 1 <= j <= L-l
        #
        # As we have to "universalize" that for all l's, we add an additional indirection and map to above
        # in map_immediate_sym

        # below is 1-1 translated code from export_metadata_bootstrap_dot_product in serialize.cpp,
        # with additional outer loop make universal
        for l in range(nQ - 1):  # noqa E741
            for j in range(nQ):
                for i in range(l + 1):
                    q_over_qi_mod_qj = 1
                    # UNUSED? inv_q_over_qi_mod_qi = 1
                    for k in range(nQ):
                        # qhat_mod_qi = q/qi (mod qi)
                        if k != i:
                            q_over_qi_mod_qj = (q_over_qi_mod_qj * q_i[k]) % q_i[j]
                    immediates.sym_immediate_map[f"base_change_matrix_{l}_{i}_{j}"] = hud.convert_to_montgomery(q_over_qi_mod_qj, q_i[j])
                    if i == j:
                        immediates.sym_immediate_map[f"inv_punctured_prod_{l}_{i}"] = hud.convert_to_montgomery(
                            pow(q_over_qi_mod_qj, -1, q_i[i]), q_i[i]
                        )

    return immediates


def extract_polys(test_vector: hpd.TestVector) -> hpd.DataPolynomials:
    """
    Helper function to extract polys
    """
    polys = hpd.DataPolynomials()
    for sym, val in test_vector.sym_data_map.items():
        transform_and_flatten_dcrtpoly(f"{sym}", val.dcrtpoly, polys.data.sym_poly_map)

    return polys


def transform_and_flatten_key_switch(
    context: hpd.FHEContext,
    prefix: str,
    key_switch: hpd.KeySwitch,
    sym_poly_map: dict[str, hpd.RNSPolynomial],
):
    # NOTE psim and kernels expect flattening not in natural hierarchical
    # version, so we cannot call transform transform_and_flatten_ciphertext but
    # have to do two-level unrol
    for d, digit in enumerate(key_switch.digits):
        for p, poly in enumerate(digit.polys):
            transform_and_flatten_poly(f"{prefix}_{p}_{d}", poly, sym_poly_map)


def transform_and_flatten_ciphertext(
    context: hpd.FHEContext,
    prefix: str,
    ciphertext: hpd.Ciphertext,
    sym_poly_map: dict[str, hpd.RNSPolynomial],
):
    for p, poly in enumerate(ciphertext.polys):
        transform_and_flatten_poly(f"{prefix}_{p}", poly, sym_poly_map)


def transform_and_flatten_dcrtpoly(
    prefix: str,
    dcrtpoly: hpd.DCRTPoly,
    sym_poly_map: dict[str, hpd.RNSPolynomial],
):
    for p, poly in enumerate(dcrtpoly.polys):
        transform_and_flatten_poly(f"{prefix}_{p}", poly, sym_poly_map)


def transform_and_flatten_plaintext(
    context: hpd.FHEContext,
    prefix: str,
    plaintext: hpd.Plaintext,
    sym_poly_map: dict[str, hpd.RNSPolynomial],
):
    transform_and_flatten_poly(f"{prefix}", plaintext.poly, sym_poly_map)


def transform_and_flatten_poly(
    prefix: str,
    poly: hpd.Polynomial,
    sym_poly_map: dict[str, hpd.RNSPolynomial],
):
    # print(f"DEBUG (TRACE): transform_and_flatten_poly(...{prefix}...)", file=sys.stderr)
    for r, rns in enumerate(poly.rns_polys):
        rns_poly = sym_poly_map[f"{prefix}_{r}"]
        rns_poly.coeffs.extend(hud.convert_to_montgomery(coeff, rns.modulus) for coeff in rns.coeffs)
        hud.poly_bit_reverse_inplace(rns_poly)
