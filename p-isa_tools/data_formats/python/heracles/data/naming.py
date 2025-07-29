# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import re
import regex_spm
import sys
import heracles.proto.common_pb2 as hpc
import heracles.proto.data_pb2 as hpd
import heracles.proto.fhe_trace_pb2 as hpf
import heracles.util.data as hud

# SYMBOL MAPPING
# =====================


def map_mem_sym(
    context: hpd.FHEContext, instr: hpf.Instruction, sym_obj_name: str
) -> str:
    """
    Map potentially symbols used in kernels as register arguments pointing to (polynomial) memory from non-universal from to a universal one.
    Note this includes both "normal" source and destination arguments from FHE operation as well as meta-data such as keys or (i)psis for negative wrapped convolution in (i)ntt
    `sym_obj_name` is string returned from function `sym_get_obj_name` applied to flattened (sub-)object names found in lower-level traces
    """
    # TODO: Actual implementation likely in C++ as we need same function also eventually there
    #    and to have only single implementation (via native code invocation from python) would
    #    be easier and more robust to maintain

    args = instr.args
    q_size = (
        context.q_size
        if context.q_size > 0
        else context.key_rns_num - context.digit_size
    )

    args_src = args.srcs  # getattr(args, args.WhichOneof("op_specific"))
    args_dest = args.dests  # getattr(args, args.WhichOneof("op_specific_dest"))

    match sym_obj_name:
        # rules for "normal" arguments
        case "output":
            mapped_sym_obj_name = args_dest[0].symbol_name
        case "c" | "input":
            mapped_sym_obj_name = args_src[0].symbol_name
        case "d" | "p":
            mapped_sym_obj_name = args_src[1].symbol_name
        # rules for meta data
        case "psi" | "ipsi":
            # See comments in extract_metadata_polys why we do this additional safety check
            mapped_sym_obj_name = f'{sym_obj_name}_{"default"}'
        case "ipsi_rot":
            # See comments in extract_metadata_polys why we do this additional safety check
            mapped_sym_obj_name = f"ipsi_{map_twiddle_type(context, instr)}"
        case "rlk":
            if context.scheme == hpc.SCHEME_BGV:
                mapped_sym_obj_name = f"rlk_{instr.plaintext_index}"
            else:
                mapped_sym_obj_name = f"rlk"
        case "gk":
            if context.scheme == hpc.SCHEME_BGV:
                mapped_sym_obj_name = (
                    f"gk_{instr.plaintext_index}_{args.params['galois_elt'].value}"
                )
            else:
                mapped_sym_obj_name = f"gk_{args.params['galois_elt'].value}"
        case "q_last_half":
            mapped_sym_obj_name = f"q_i_{args_dest.num_rns}_half_mod_q_j"  # in flattening we start with 0 but dest is already last-1 ..
        case _:
            mapped_sym_obj_name = sym_obj_name

    # print(f"DEBUG (TRACE): map_mem_sym(.., {sym_obj_name}) -> {mapped_sym_obj_name}", file=sys.stderr)
    return mapped_sym_obj_name


def map_immediate_sym(
    context: hpd.FHEContext, instr: hpf.Instruction, sym_imm_name: str
) -> str:
    """
    Map potentially non-universal immediate symbols used in kernels with either a universal one
    or (e.g., for `add_corrected`) an actual numerical value
    """
    # TODO: Actual implementation in C++ & native code invocation here for same reasons as mentioned for `map_mem_sym`

    if context.scheme == hpc.SCHEME_BGV:
        bgv_info = context.bgv_info
        key_rns_num = context.key_rns_num
        # NOTE: we assume _all_ keys have same digit size!!
        k = bgv_info.plaintext_specific[0].keys.relin_key.k
    match regex_spm.fullmatch_in(sym_imm_name):
        case r"^(c|d)_mont_adjusting_factor_(\d+)$" as m:
            match m[1]:
                case "c":
                    adj_factor = int(instr.args.params["adj_factor1"].value)
                case "d":
                    adj_factor = int(instr.args.params["adj_factor2"].value)
                case _:
                    assert False
            adj_factor = hud.convert_to_montgomery(adj_factor, context.q_i[int(m[2])])
            mapped_sym_imm_name = f"{adj_factor}"

        case r"^it$" as m:
            mapped_sym_imm_name = f"neg_inv_t_{instr.plaintext_index}_mod_q_i_{instr.args.srcs[0].num_rns-1}"  # in flattening we start with 0 ..

        case r"^t_inverse_mod_p_(\d+)$" as m:
            mapped_sym_imm_name = f"neg_inv_t_{instr.plaintext_index}_mod_q_i_{key_rns_num - k + int(m[1])}"  # in flattening we start with 0 ..

        case r"^iq_(\d+)$" as m:
            mapped_sym_imm_name = f"inv_q_i_{instr.args.srcs[0].num_rns-1}_mod_q_j_{m[1]}"  # in flattening we start with 0 ..

        case r"^t_(\d+)$" as m:
            mapped_sym_imm_name = f"t_{instr.plaintext_index}_mod_q_i_{m[1]}"

        case r"^pinv_q_(\d+)$" as m:
            mapped_sym_imm_name = f"inv_p_mod_q_i_{m[1]}"

        case r"^corr-inv-target-corr-q-scalar_(\d+)$" as m:
            mont_adj_factor = hud.convert_to_montgomery(
                int(instr.args.params["adj_factor1"].value), context.q_i[int(m[1])]
            )
            mapped_sym_imm_name = f"{mont_adj_factor}"

        case r"^const-reduced_(\d+)$" as m:
            adj_factor = int(instr.args.params["adj_factor1"].value)
            if bool(instr.args.params["do_invert"].value):
                adj_factor = pow(adj_factor, -1, context.q_i[int(m[1])])
            mont_adj_factor = hud.convert_to_montgomery(
                adj_factor, context.q_i[int(m[1])]
            )
            mapped_sym_imm_name = f"{mont_adj_factor}"

        case r"^BaseChangeMatrix_(\d+_\d+)$" as m:
            mapped_sym_imm_name = f"base_change_matrix_{instr.args.srcs[0].num_rns-1}_{m[1]}"  # in flattening we start with 0 ..

        case r"^InvPuncturedProd_(\d+)$" as m:
            mapped_sym_imm_name = f"inv_punctured_prod_{instr.args.srcs[0].num_rns-1}_{m[1]}"  # in flattening we start with 0 ..

        case _:
            mapped_sym_imm_name = sym_imm_name

    # print(f"DEBUG (TRACE): map_immediate_sym(.., {sym_imm_name}) -> {mapped_sym_imm_name}", file=sys.stderr)
    return mapped_sym_imm_name


def map_twiddle_type(context: hpd.FHEContext, instr: hpf.Instruction) -> str:
    """
    Map to the twiddle type used by this instruction.
    Will always a type even if instruction doesn't necessarily need twiddles.
    """

    if instr.op.lower() not in (
        "rotate",
        "boot_fastrotation_ext",
        "boot_fastrotation_ext_noaddfirst",
        "boot_galois_plain",
        "boot_conjugate",
        "boot_addrotate_c0",
    ):
        return "default"

    return instr.args.params["galois_elt"].value


# OBJECT (un)FLATTENING
# ==========================


def get_sym_obj_name(flat_sym_name: str) -> str:
    """
    Extract the symbolic name of an object from a provided flattened (polynomial-based sub-)object names as found in lower-level traces
    """
    return split_sym_name(flat_sym_name)[0]


flat_obj_syn_name_pattern = re.compile(r"^([a-zA-Z_]+)_([\d_]*)$")


def split_sym_name(flat_sym_name: str) -> tuple[str, str | None]:
    """
    Split the symbolic name of an object from a provided flattened (polynomial-based sub-)object names as found in lower-level traces into the obj name and the extension
    if the name is _not_ a name of a flattened object, the name is returned and the second element of the tuple, normally the extension, is 'None'
    """
    match = flat_obj_syn_name_pattern.match(flat_sym_name)
    if match:
        return (match.group(1), match.group(2))
    return (flat_sym_name, None)


def combine_sym_name(sym_obj_name: str, sym_obj_extension: str) -> str:
    """
    Split the symbolic name of an object from a provided flattened (polynomial-based sub-)object names as found in lower-level traces into the obj name and the extension
    """
    return f"{sym_obj_name}_{sym_obj_extension}"


# NOTE: To make flattened names more readable/robust, the naming might change to
#
#       a. keyname: keys -> { keyname_d${digitnum}:  ciphertext }  // _d for digit
#       b. ctxtname: ciphertext -> {ctxtname_p${polynum}: polynomial } // _p for number of (full) polynomial (=degree) of ciphertext
#       c. polyname: polynomial -> {polyname_r${rnsnum}: rns32polynomial } # arbitrary size rns32 polys with _r for rns
#       d. rnsname: rns32polynomial -> {rnsname_c${chunkname}: rns32/8kpolynomial chunks with _c for chunk
#
#   Above has to be applied recursively to required depth -- depending on consumer transformation d. is not alwaysneeded ... --  with results
#   the union of intermediary sets, i.e., only resulting in a single set, not sets of sets.
#   E.g., a ciphertext ctx mapped to level d with name c would result in set { c_p$P_r$R_c$C : ctx.poly[$P].rns-poly[$R].chunk[$C]
#   with $P, $R & $C ranging over the size of the corresponding dimension}.
#
#   Whether we change that or not depends whether on how much "parallel" change happen in psim & kernels.
#   Once that would be in, it probably also makes sense to add a more complete decomposition function along the lines of
#
#         def decompose_flat_sym_name(flat_sym_name: str) -> (str, type, digit, poly, rns, chunk):


# TODO: Consider adding some object flattening and de-flattening functions.
#
#    E.g., something like
#         def poly2rnspoly(symbol: str, poly: Polynomial) -> dict[str, RNSPolynomial]:
#    and/or
#        def poly2rnspoly(dict[str, Polynomial]) -> dict[str, RNSPolynomial]:
#    for batch mode and related functions also for KeySwitch, Ciphertext and Plaintext instead of Polynomial.
#
#    For treating results, i.e., outputs from HEC, we might eventually also need inverse functions
#
#    As part of swizzling and un-swizzling, we also have to flatten and unflatten RNSPolynomials to/from (sets of) HECBasePolynomials,
#    so some related functions could also be useful.
#
#    Will add them on-demand as need arises ...
