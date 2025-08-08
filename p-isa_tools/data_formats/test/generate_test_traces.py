#!/usr/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Generate test trace files for heracles_test.py
This replaces the need for C++ test to generate these files.
"""

import heracles.data.io as hdi
import heracles.fhe_trace.io as hfi
import heracles.proto.common_pb2 as hpc
import heracles.proto.data_pb2 as hpd
import heracles.proto.fhe_trace_pb2 as hpf


def generate_program_trace():
    """Generate test.program_trace file matching the C++ test."""
    # Create sample trace
    trace = hpf.Trace()

    # Set context
    trace.scheme = hpc.SCHEME_BGV
    trace.key_rns_num = 70
    trace.N = 16384

    # First instruction - NEGATE
    negate = trace.instructions.add()
    negate.op = "NEGATE"
    negate.plaintext_index = 2

    # NEGATE destination
    neg_dest = negate.args.dests.add()
    neg_dest.symbol_name = "t1"
    neg_dest.num_rns = 5
    neg_dest.order = 2

    # NEGATE source
    neg_src = negate.args.srcs.add()
    neg_src.symbol_name = "in1"
    neg_src.num_rns = 5
    neg_src.order = 2

    # Second instruction - ADD
    add = trace.instructions.add()
    add.op = "ADD"
    add.plaintext_index = 2

    # ADD destination
    add_dest = add.args.dests.add()
    add_dest.symbol_name = "out1"
    add_dest.num_rns = 5
    add_dest.order = 2

    # ADD sources
    add_src1 = add.args.srcs.add()
    add_src1.symbol_name = "t1"
    add_src1.num_rns = 5
    add_src1.order = 2

    add_src2 = add.args.srcs.add()
    add_src2.symbol_name = "in2"
    add_src2.num_rns = 5
    add_src2.order = 2

    # Save the trace
    hfi.store_trace("test.program_trace", trace)
    print("Generated test.program_trace")

    return trace


def generate_data_trace():
    """Generate test.data_trace file (context and test vector)."""
    # Create FHE context
    context = hpd.FHEContext()
    context.scheme = hpc.SCHEME_BGV
    context.N = 16384
    context.key_rns_num = 70
    context.q_size = 5

    # Add some basic BGV-specific information
    bgv_spec = context.bgv_info

    # Add a plaintext specification (index 2 as used in the trace)
    pt_spec = bgv_spec.plaintext_specific.add()
    pt_spec.plaintext_modulus = 65537
    pt_spec = bgv_spec.plaintext_specific.add()
    pt_spec.plaintext_modulus = 65537
    pt_spec = bgv_spec.plaintext_specific.add()  # Index 2
    pt_spec.plaintext_modulus = 65537

    # Create TestVector with some sample data
    testvector = hpd.TestVector()

    # Add data for symbols used in the trace
    for symbol in ["in1", "in2", "t1", "out1", "output_0_1_2"]:
        data = testvector.sym_data_map[symbol]

        # Add a simple DCRTPoly (the Data message only has dcrtpoly field)
        dcrt = data.dcrtpoly
        dcrt.in_ntt_form = True

        # Add polynomial data (2 for ciphertext order)
        for _ in range(2):  # 2 polynomials for a ciphertext
            poly = dcrt.polys.add()
            poly.in_OpenFHE_EVALUATION = False

            # Add RNS polynomials (5 moduli as specified in trace)
            for _ in range(5):
                poly.rns_polys.add()
                # Just create empty RNS polynomial structure

    # Save the data trace
    hdi.store_data_trace("test.data_trace", context, testvector)
    print("Generated test.data_trace and associated files")

    return context, testvector


def main():
    """Generate all test trace files."""
    print("Generating test trace files...")

    # Generate the program trace
    generate_program_trace()

    # Generate the data trace
    generate_data_trace()

    print("\nTest trace generation complete!")
    print("Files created:")
    print("  - test.program_trace")
    print("  - test.data_trace (manifest)")
    print("  - test.data_trace_hec_context_part_0")
    print("  - test.data_trace_testvector_part_0")

    # Verify the files can be loaded
    print("\nVerifying files can be loaded...")
    hfi.load_trace("test.program_trace")
    hdi.load_hec_context("test.data_trace")
    hdi.load_data_trace("test.data_trace")
    print("✓ All files loaded successfully")


if __name__ == "__main__":
    main()
