#!/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# does not work standalone unless PYTHONPATH is modified
# runs only with ```ctest``` inside build directory
import heracles.proto.common_pb2 as hpc
import heracles.proto.fhe_trace_pb2 as hpf
import google.protobuf.json_format as gpj
import heracles.fhe_trace.io as hfi
import heracles.data.io as hdi
import heracles.data.naming as hdn


def test():
    # simulate interaction of program mapper with this library ....
    trace = hfi.load_trace("test.program_trace")
    hec_context = hdi.load_hec_context("test.data_trace")
    # Note: for this to succeed, you will have to previously have run the C++ `heracles_test` test program
    for fhe_instr in trace.instructions:
        # find compiled kernel for operation fhe_instr.op and for each HEC-ISA instruction in kernel ..
        # .. find all memory and immediate symbols ...
        flat_obj_sym = "output_0_1_2"
        mem_sym_prefix = hdn.get_sym_obj_name(flat_obj_sym)
        immediate_sym = "meta_7"
        # ... and their universal form  ...
        # (Note: first call is a replacement, with slightly different arguments, of the `replace_symbols` function from Sim0.5.1 `program_mapper.py`))
        universal_mem_sym_prefix = hdn.map_mem_sym(
            hec_context, fhe_instr, mem_sym_prefix
        )
        # TODO: hdn.map_immediate_sym will fail until heracles_test.cpp exports a full context with
        #   keys so far just skip ...
        universal_immediate_sym = None
        # universal_immediate_sym = hdn.map_immediate_sym(
        #    hec_context, fhe_instr, immediate_sym
        # )
        # ... and in kernel ...
        print(
            f"replace for operation '{fhe_instr.op}' memory symbol-prefix '{mem_sym_prefix}' with '{universal_mem_sym_prefix}' and immediate symbol-prefix '{immediate_sym}' with '{universal_immediate_sym}'"
        )

    # complete dump ...
    print(trace)
    print(gpj.MessageToJson(trace))
    print(gpj.MessageToDict(trace))

    # selective access to trace information ...
    print(
        f"scheme num={trace.scheme} / "
        f"default-string={hpc.Scheme.DESCRIPTOR.values_by_number[trace.scheme].name} / "
        f"friendly-string={hpc.Scheme.DESCRIPTOR.values_by_number[trace.scheme].GetOptions()}"
    )  # TODO: extract heracles.instruction.string_name extension
    first_instr = trace.instructions[0]
    src1 = first_instr.args.srcs[0].symbol_name
    src2 = (
        first_instr.args.srcs[1].symbol_name
        if len(first_instr.args.srcs) > 1
        else "N/A"
    )

    dest = first_instr.args.dests[0].symbol_name
    print(
        f"first instruction arguments: destination '{dest}', src1='{src1}', src2='{src2}'"
    )
    second_instr = trace.instructions[1]
    src1 = second_instr.args.srcs[0].symbol_name
    src2 = (
        second_instr.args.srcs[1].symbol_name
        if len(second_instr.args.srcs) > 1
        else "N/A"
    )

    dest = second_instr.args.dests[0].symbol_name

    print(
        f"second instruction arguments: destination '{dest}', src1='{src1}', src2='{src2}'"
    )

    return 0


if __name__ == "__main__":
    test()
