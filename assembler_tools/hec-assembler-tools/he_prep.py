#! /usr/bin/env python3

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
This module provides functionality for preprocessing P-ISA abstract kernels before further assembling for HERACLES.

Functions:
    save_pisa_listing(out_stream, instr_listing: list)
        Stores instructions to a stream in P-ISA format.

    main(args)
        Preprocesses the P-ISA kernel using parsed CLI args.

    parse_args() -> argparse.Namespace
        Parses command-line arguments for the preprocessing script.

Usage:
    This script is intended to be run as a standalone program. It requires specific command-line
    arguments to specify input and output files and verbosity options for the preprocessing process.

Contributors to the assembler that are not reflected in the Git history
(sorted by last name): Avinash Alevoor, Rashmi Agrawal, Suvadeep Banerje,
Flavio Bergamaschi, Jeremy Bottleson, Jack Crawford, Hamish Hunt,
Michael Steiner, Kylan Race, Ernesto Zamora Ramos, Jose Rojas, Adish Vartak
Wen Wang, Chris Wilkerson, and Minxuan Zhou.
"""

import argparse
import os
import time

from assembler.common import constants
from assembler.memory_model import MemoryModel
from assembler.spec_config.isa_spec import ISASpecConfig
from assembler.spec_config.mem_spec import MemSpecConfig
from assembler.stages.prep import preprocessor
from assembler.stages.prep.data_splits import DataSplits


def save_pisa_listing(out_stream, instr_listing: list):
    """
    Stores the instructions to a stream in P-ISA format.

    This function iterates over a list of instructions and prints each instruction in P-ISA format
    to the specified output stream.

    Args:
        out_stream: The output stream to which the instructions are printed.
        instr_listing (list): A list of instructions to be printed in P-ISA format.

    Returns:
        None
    """
    for inst in instr_listing:
        inst_line = inst.to_pisa_format()
        if inst_line:
            print(inst_line, file=out_stream)


def _preprocess_and_save(insts, output_file_name: str, b_verbose: bool) -> tuple[str, int, float]:
    """Preprocess P-ISA kernel (bank assign + save) and return (output_file_name, num_input_instr, elapsed_sec)."""

    hec_mem_model = MemoryModel(
        constants.MemoryModel.HBM.MAX_CAPACITY_WORDS,
        constants.MemoryModel.SPAD.MAX_CAPACITY_WORDS,
        constants.MemoryModel.NUM_REGISTER_BANKS,
    )
    start_time = time.time()
    insts_listing = preprocessor.preprocess_pisa_kernel_listing(hec_mem_model, insts, progress_verbose=b_verbose)
    num_input_instr = len(insts_listing)
    if b_verbose:
        print("Assigning register banks to variables...")
    preprocessor.assign_register_banks_to_vars(hec_mem_model, insts_listing, use_bank0=False, verbose=b_verbose)
    elapsed = time.time() - start_time
    if b_verbose:
        print("Saving...")
    with open(output_file_name, "w", encoding="utf-8") as outnum:
        save_pisa_listing(outnum, insts_listing)
    if b_verbose:
        print(f"Output: {output_file_name}")
        print(f"Instructions in input: {num_input_instr}")
        print(f"Instructions in output: {len(insts_listing)}")
        print(f"--- Generation time: {elapsed} seconds ---")
    return output_file_name, num_input_instr, elapsed


def main(args):
    """Preprocess the P-ISA kernel using parsed CLI args.

    Args:
        args (argparse.Namespace): Must contain at least
            - input_file_name
            - output_file_name
            - mem_file
            - verbose
    """
    sub_kernels: list[tuple[list[int], str]] = []
    if args.split_on:
        print("Parsing instructions...")
        with open(args.input_file_name, encoding="utf-8") as insts:
            insts_listing = preprocessor.parse_pisa_kernel_from_lines(insts)
        print("Parsed instructions, building dependency graphs...")
        mem_info = DataSplits()
        dinstrs = mem_info.load_mem_file(args.mem_file)
        instrs_graphs = mem_info.build_instrs_dependency_graph(insts_listing)
        print("Built dependency graphs.")
        instr_sets, externals = mem_info.get_isolated_instrs_splits(instrs_graphs, insts_listing, 4000, 1000)
        new_inouts = None
        if instr_sets is None:
            instr_sets, externals, new_inouts = mem_info.get_community_instrs_splits(instrs_graphs, insts_listing, 4000, 1000)
            if instr_sets is None:
                raise RuntimeError("Could not split instructions into sets that fit memory constraints.")

        if not args.output_file_name:
            root, ext = os.path.splitext(args.input_file_name)
            middle = ".tw"
        else:
            root, ext = os.path.splitext(args.output_file_name)
            middle = ""

        mem_info.split_mem_info(args.mem_file, dinstrs, externals, new_inouts)

        print(f"Generated {len(instr_sets)} sub-kernels. Externals per sub-kernel: {[len(e) for e in externals]}")
        for inst_idx, instr_set in enumerate(instr_sets):
            output_file_name = root + f"{middle}_{inst_idx}" + ext
            # output_mem_fname = mem_root + f"_{inst_idx}" + mem_ext
            # if new_inouts:
            #    mem_info.write_mem_file(output_mem_fname, dinstrs, externals[inst_idx], new_inouts[inst_idx])
            # else:
            #    mem_info.write_mem_file(output_mem_fname, dinstrs, externals[inst_idx])

            lines: list[int] = []
            for idx in sorted(instr_set):
                line = mem_info.to_raw_pisa_format(insts_listing[idx])
                lines.append(line)
            sub_kernels.append((lines, output_file_name))

    else:
        if not args.output_file_name:
            root, ext = os.path.splitext(args.input_file_name)
            output_file_name = root + ".tw" + ext
        else:
            output_file_name = args.output_file_name

        lines: list[int] = []
        with open(args.input_file_name, encoding="utf-8") as insts:
            lines = insts.readlines()
        sub_kernels.append((lines, output_file_name))

    for insts, out_file in sub_kernels:
        _preprocess_and_save(insts, out_file, (args.verbose > 1))


def parse_args():
    """
    Parses command-line arguments for the preprocessing script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "HERACLES Assembling Pre-processor.\n"
            "This program performs the preprocessing of P-ISA abstract kernels before further assembling."
        )
    )
    parser.add_argument(
        "input_file_name",
        help="Input abstract kernel file to which to add twiddle factors.",
    )
    parser.add_argument(
        "output_file_name",
        nargs="?",
        help="Output file name. Defaults to <input_file_name_no_ext>.tw.<input_file_name_ext>",
    )
    parser.add_argument(
        "--isa_spec",
        default="",
        dest="isa_spec_file",
        help=("Input ISA specification (.json) file."),
    )
    parser.add_argument(
        "--mem_spec",
        default="",
        dest="mem_spec_file",
        help=("Input Mem specification (.json) file."),
    )
    parser.add_argument(
        "--mem_file",
        default="",
        dest="mem_file",
        help=("Input Mem file (.mem) file."),
    )
    parser.add_argument(
        "--split_on",
        default="",
        action="store_true",
        dest="split_on",
        help=("Enable automatic splitting when its estimated usage exceeds memory limits."),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="count",
        default=0,
        help=(
            "If enabled, extra information and progress reports are printed to stdout. "
            "Increase level of verbosity by specifying flag multiple times, e.g. -vv"
        ),
    )
    p_args = parser.parse_args()

    return p_args


if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)

    args = parse_args()

    args.isa_spec_file = ISASpecConfig.initialize_isa_spec(module_dir, args.isa_spec_file)
    args.mem_spec_file = MemSpecConfig.initialize_mem_spec(module_dir, args.mem_spec_file)

    if args.verbose > 0:
        print(module_name)
        print()
        print(f"Input: {args.input_file_name}")
        print(f"Output: {args.output_file_name}")
        print(f"Mem File: {args.mem_file}")
        print(f"ISA Spec: {args.isa_spec_file}")
        print(f"Mem Spec: {args.mem_spec_file}")
        print(f"Split On: {args.split_on}")

    main(args)

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
