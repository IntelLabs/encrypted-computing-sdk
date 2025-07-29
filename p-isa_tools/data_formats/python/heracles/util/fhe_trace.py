# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright (C) 2024 Intel Corporation

import heracles.proto.fhe_trace_pb2 as hpf


def get_all_symbols(trace: hpf.Trace, get_intermediates: bool = False):
    syms_input = set()
    syms_output = set()
    syms_intermediate = set()
    for instruction in trace.instructions:
        if instruction.op.startswith("bk_"):
            continue

        for src in instruction.args.srcs:
            syms_input.add(src.symbol_name)
        for dest in instruction.args.dests:
            syms_output.add(dest.symbol_name)

    if get_intermediates:
        # get pure inputs
        syms_input_exclusive = syms_input - syms_output
        # get intermediates
        syms_intermediate = syms_input - syms_input_exclusive
        # get pure outputs
        syms_output = syms_output - syms_intermediate
        syms_input = syms_input_exclusive

    return [syms_input, syms_output, syms_intermediate]
