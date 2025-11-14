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
from assembler.common.config import GlobalConfig
from assembler.memory_model import MemoryModel
from assembler.spec_config.isa_spec import ISASpecConfig
from assembler.spec_config.mem_spec import MemSpecConfig
from assembler.stages.prep import preprocessor
from assembler.stages.prep.kernel_splitter import KernelSplitter


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


def main(args):
    """Preprocess the P-ISA kernel using parsed CLI args.

    Args:
        args (argparse.Namespace): Must contain at least
            - input_file_name
            - output_file_name
            - mem_file
            - verbose
        optional:
            - strategy
            - interchange
    """

    strategy = getattr(args, "strategy", "largest_first")
    interchange = getattr(args, "interchange", False)

    GlobalConfig.debugVerbose = args.verbose

    # used for timings
    insts_end: float = 0.0

    start_time = time.time()
    hec_mem_model = MemoryModel(
        constants.MemoryModel.HBM.MAX_CAPACITY_WORDS,
        constants.MemoryModel.SPAD.MAX_CAPACITY_WORDS,
        constants.MemoryModel.NUM_REGISTER_BANKS,
    )

    insts_listing = []
    start_time = time.time()
    # read input kernel and pre-process P-ISA:
    # resulting instructions will be correctly transformed and ready to be converted into ASM-ISA instructions;
    # variables used in the kernel will be automatically assigned to banks.
    with open(args.input_file_name, encoding="utf-8") as insts:
        insts_listing = preprocessor.preprocess_pisa_kernel_listing(hec_mem_model, insts)
    num_input_instr: int = len(insts_listing)  # track number of instructions in input kernel
    if args.verbose > 0:
        print("Assigning register banks to variables...")
    preprocessor.assign_register_banks_to_vars(
        hec_mem_model,
        insts_listing,
        use_bank0=False,
        strategy=strategy,
        interchange=interchange,
    )

    # Determine output file name
    if not args.output_file_name:
        root, ext = os.path.splitext(args.input_file_name)
        args.output_file_name = root + ".tw" + ext

    sub_kernels: list[tuple[list[int], str]] = []
    if args.split_on:
        kern_splitter = KernelSplitter()
        split_entries = kern_splitter.prepare_instruction_splits(args, insts_listing)
        sub_kernels.extend(split_entries)
    else:
        sub_kernels.append((insts_listing, args.output_file_name))

    insts_end = time.time() - start_time

    if args.verbose > 0:
        print(f"\nInstructions in input: {num_input_instr}")

    # Write sub-kernels
    if args.verbose > 0:
        print("\tSaving...")
    for insts, out_file in sub_kernels:
        with open(out_file, "w", encoding="utf-8") as out_split:
            save_pisa_listing(out_split, insts)
        if args.verbose > 0:
            print(f"\tOutput: {out_file}")
            print(f"\tInstructions in output: {len(insts)}")

    if args.verbose > 0:
        print(f"--- Generation time: {insts_end} seconds ---")


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
        "--split_vars_limit",
        type=float,
        default=float("inf"),
        dest="split_vars_limit",
        help="Maximum variable footprint allowed when splitting.",
    )
    parser.add_argument(
        "--split_inst_limit",
        type=float,
        default=float("inf"),
        dest="split_inst_limit",
        help="Maximum instructions per split when splitting.",
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
    parser.add_argument(
        "--strategy",
        default="largest_first",
        help="Strategy for greedy coloring algorithm. Defaults to 'largest_first'.",
    )
    parser.add_argument(
        "--interchange",
        action="store_true",
        default=False,
        help="Whether to use interchange in greedy coloring. Defaults to False.",
    )
    p_args = parser.parse_args()
    p_args.split_on = bool(p_args.split_inst_limit != float("inf") or p_args.split_vars_limit != float("inf"))
    if p_args.split_on:
        assert p_args.mem_file, "--mem_file must be specified when --split_on is used."

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
        print(f"Split Inst Limit: {args.split_inst_limit}")
        print(f"Split Vars Limit: {args.split_vars_limit}")
        print(f"Split On: {args.split_on}")
        print(f"Graph Coloring Strategy: {args.strategy}")
        print(f"Graph Coloring Interchange: {args.interchange}")

    main(args)

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
