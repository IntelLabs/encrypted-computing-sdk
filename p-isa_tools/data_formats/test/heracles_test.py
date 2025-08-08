#!/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from pathlib import Path

# Setup: Ensure protos are compiled and test data exists
test_dir = Path(__file__).parent.absolute()
proto_dir = test_dir.parent / "python" / "heracles" / "proto"

# Check and compile protos if needed
proto_files = ["common_pb2.py", "data_pb2.py", "fhe_trace_pb2.py", "maps_pb2.py"]
if not proto_dir.exists() or not all((proto_dir / f).exists() for f in proto_files):
    print("Proto files not found, compiling...")
    try:
        import compile_protos

        sys.path.insert(0, str(test_dir))
        compile_protos.compile_protos()
    except ImportError:
        print("ERROR: grpcio-tools not found. Install with: pip install -e '.[dev]'")
        sys.exit(1)

# Add python directory to path
sys.path.insert(0, str(test_dir.parent / "python"))

# Check and generate test traces if needed
os.chdir(test_dir)
if not os.path.exists("test.program_trace") or not os.path.exists("test.data_trace"):
    print("Generating test traces...")
    import generate_test_traces

    generate_test_traces.main()

# Now import the modules (after setup is complete)
import google.protobuf.json_format as gpj  # noqa: E402
import heracles.data.io as hdi  # noqa: E402
import heracles.data.naming as hdn  # noqa: E402
import heracles.fhe_trace.io as hfi  # noqa: E402
import heracles.proto.common_pb2 as hpc  # noqa: E402


def test():
    # simulate interaction of program mapper with this library ....
    # Test data is already generated at module import time
    trace = hfi.load_trace("test.program_trace")
    hec_context = hdi.load_hec_context("test.data_trace")

    for fhe_instr in trace.instructions:
        # find compiled kernel for operation fhe_instr.op and for each HEC-ISA instruction in kernel ..
        # .. find all memory and immediate symbols ...
        flat_obj_sym = "output_0_1_2"
        mem_sym_prefix = hdn.get_sym_obj_name(flat_obj_sym)
        immediate_sym = "meta_7"
        # ... and their universal form  ...
        # (Note: first call is a replacement, with slightly different arguments,
        # of the `replace_symbols` function from Sim0.5.1 `program_mapper.py`))
        universal_mem_sym_prefix = hdn.map_mem_sym(hec_context, fhe_instr, mem_sym_prefix)
        # TODO: hdn.map_immediate_sym will fail until heracles_test.cpp exports a full context with
        #   keys so far just skip ...
        universal_immediate_sym = None
        # universal_immediate_sym = hdn.map_immediate_sym(
        #    hec_context, fhe_instr, immediate_sym
        # )
        # ... and in kernel ...
        print(
            f"replace for operation '{fhe_instr.op}' memory symbol-prefix '{mem_sym_prefix}'"
            f" with '{universal_mem_sym_prefix}' and immediate symbol-prefix '{immediate_sym}' with '{universal_immediate_sym}'"
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
    src2 = first_instr.args.srcs[1].symbol_name if len(first_instr.args.srcs) > 1 else "N/A"

    dest = first_instr.args.dests[0].symbol_name
    print(f"first instruction arguments: destination '{dest}', src1='{src1}', src2='{src2}'")
    second_instr = trace.instructions[1]
    src1 = second_instr.args.srcs[0].symbol_name
    src2 = second_instr.args.srcs[1].symbol_name if len(second_instr.args.srcs) > 1 else "N/A"

    dest = second_instr.args.dests[0].symbol_name

    print(f"second instruction arguments: destination '{dest}', src1='{src1}', src2='{src2}'")


if __name__ == "__main__":
    test()
