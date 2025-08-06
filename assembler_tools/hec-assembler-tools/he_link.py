#! /usr/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file he_link.py
@brief This module provides functionality for linking assembled kernels into a full HERACLES program for execution queues: MINST, CINST, and XINST.

@par Classes:
    - LinkerRunConfig: Maintains the configuration data for the run.
    - KernelInfo: Structure for kernel files.

@par Functions:
    - main(run_config: LinkerRunConfig, verbose_stream=None): Executes the linking process using the provided configuration.
    - parse_args() -> argparse.Namespace: Parses command-line arguments for the linker script.

@par Usage:
    This script is intended to be run as a standalone program. It requires specific command-line arguments
    to specify input and output files and configuration options for the linking process.
"""

import argparse
import os
import sys
import warnings

from assembler.common.config import GlobalConfig
from assembler.common.counter import Counter
from assembler.spec_config.isa_spec import ISASpecConfig
from assembler.spec_config.mem_spec import MemSpecConfig
from linker.he_link_utils import (
    NullIO,
    initialize_memory_model,
    prepare_input_files,
    prepare_output_files,
    remap_vars,
    update_input_prefixes,
)
from linker.instructions import BaseInstruction
from linker.kern_trace.trace_info import TraceInfo
from linker.linker_run_config import LinkerRunConfig
from linker.loader import Loader
from linker.steps import program_linker
from linker.steps.variable_discovery import check_unused_variables, scan_variables


def main(run_config: LinkerRunConfig, verbose_stream=NullIO()):
    """
    @brief Executes the linking process using the provided configuration.

    This function prepares input and output file names, initializes the memory model, discovers variables,
    and links each kernel, writing the output to specified files.

    @param run_config The configuration object containing run parameters.
    @param verbose_stream The stream to which verbose output is printed. Defaults to NullIO.

    @return None
    """
    if run_config.use_xinstfetch:
        warnings.warn("Ignoring configuration flag 'use_xinstfetch'.")

    # Update global config
    GlobalConfig.hasHBM = run_config.has_hbm
    GlobalConfig.suppress_comments = run_config.suppress_comments

    # Process trace file if enabled
    kernel_ops = []
    if run_config.using_trace_file:
        kernel_ops = TraceInfo.parse_kernel_ops_from_file(run_config.trace_file)
        update_input_prefixes(kernel_ops, run_config)

        print(
            f"Found {len(kernel_ops)} kernel ops in trace file:",
            file=verbose_stream,
        )

        print("", file=verbose_stream)

    # Prepare input and output files
    program_info = prepare_output_files(run_config)
    kernels_info = prepare_input_files(run_config, program_info)

    # Reset counters
    Counter.reset()

    # Parse memory information and setup memory model
    print("Linking...", file=verbose_stream)
    print("", file=verbose_stream)
    print("Interpreting variable meta information...", file=verbose_stream)

    # Process kernel DInstructions when using trace file
    program_dinstrs = []
    if run_config.using_trace_file:
        dinstrs_per_kernel = []
        for kernel_info in kernels_info:
            kernel_dinstrs = Loader.load_dinst_kernel_from_file(kernel_info.mem)
            dinstrs_per_kernel.append(kernel_dinstrs)

        remap_vars(kernels_info, dinstrs_per_kernel, kernel_ops, verbose_stream)

        # Concatenate all mem info objects into one
        program_dinstrs = program_linker.LinkedProgram.join_dinst_kernels(dinstrs_per_kernel)

        # Write new program memory model to an output file
        if program_info.mem is None:
            raise RuntimeError("Output memory file path is None")
        BaseInstruction.dump_instructions_to_file(program_dinstrs, program_info.mem)

    # Initialize memory model
    mem_model = initialize_memory_model(run_config, program_dinstrs, verbose_stream)

    # Discover variables
    print("  Finding all program variables...", file=verbose_stream)
    print("  Scanning", file=verbose_stream)

    scan_variables(kernels_info=kernels_info, mem_model=mem_model, verbose_stream=verbose_stream)

    check_unused_variables(mem_model)

    print(f"    Variables found: {len(mem_model.variables)}", file=verbose_stream)
    print("Linking started", file=verbose_stream)

    # Link kernels and generate outputs
    program_linker.LinkedProgram.link_kernels_to_files(kernels_info, program_info, mem_model, verbose_stream=verbose_stream)

    # Flush cached kernels
    Loader.flush_cache()

    print("Output written to files:", file=verbose_stream)
    print("  ", program_info.minst, file=verbose_stream)
    print("  ", program_info.cinst, file=verbose_stream)
    print("  ", program_info.xinst, file=verbose_stream)
    if run_config.using_trace_file:
        print("  ", program_info.mem, file=verbose_stream)


def parse_args():
    """
    @brief Parses command-line arguments for the linker script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    @return argparse.Namespace Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "HERACLES Linker.\n"
            "Links assembled kernels into a full HERACLES program "
            "for each of the three execution queues: MINST, CINST, and XINST.\n\n"
            "To link several kernels, specify each kernel's input prefix in order. "
            "Variables that should carry on across kernels should be have the same name. "
            "Linker will recognize matching variables and keep their values between kernels. "
            "Variables that are inputs and outputs (and metadata) for the whole program must "
            "be indicated in the input memory mapping file."
        )
    )
    parser.add_argument(
        "-ip",
        "--input_prefixes",
        dest="input_prefixes",
        nargs="+",
        help=(
            "List of input prefixes. For an input prefix, linker will "
            "assume three files exist named `<prefix[i]>.minst`, "
            "`<prefix[i]>.cinst`, and `<prefix[i]>.xinst`."
        ),
    )
    parser.add_argument(
        "--mem_spec",
        default="",
        dest="mem_spec_file",
        help=("Input Mem specification (.json) file."),
    )
    parser.add_argument(
        "--isa_spec",
        default="",
        dest="isa_spec_file",
        help=("Input ISA specification (.json) file."),
    )
    parser.add_argument(
        "--use_trace_file",
        default="",
        dest="trace_file",
        help=(
            "Instructs the linker to use a trace file to determine the required input files for each kernel line. "
            "The linker will look for the following files: *.minst, *.cinst, *.xinst, and *.mem. "
            "When this flag is set, the 'input_mem_file' and 'input_prefixes' flags are ignored."
        ),
    )
    parser.add_argument(
        "-id",
        "--input_dir",
        dest="input_dir",
        default="",
        help=(
            "Directory where input files are located. "
            "If not provided and use_trace_file is set, the directory of the trace file will be used. "
            "This is useful when input files are in a different location than the trace file. "
            "If not provided and use_trace_file is not set, the current working directory will be used."
        ),
    )
    parser.add_argument(
        "-im",
        "--input_mem_file",
        dest="input_mem_file",
        required=False,
        default="",
        help=(
            "Input memory mapping file associated with the resulting program. "
            "Specifies the names for input, output, and metadata variables for a single kernel"
            " or also a full program if instead this is used to link multiple kernels together."
        ),
    )
    parser.add_argument(
        "-o",
        "--output_prefix",
        dest="output_prefix",
        required=True,
        help=(
            "Prefix for the output file names. "
            "Three files will be generated: \n"
            "`output_dir/output_prefix.minst`, `output_dir/output_prefix.cinst`, and "
            "`output_dir/output_prefix.xinst`. \n"
            "Output filenames cannot match input file names."
        ),
    )
    parser.add_argument(
        "-od",
        "--output_dir",
        dest="output_dir",
        default="",
        help=(
            "Directory where to store all intermediate files and final output. "
            "This will be created if it doesn't exists. "
            "Defaults to current working directory."
        ),
    )
    parser.add_argument("--hbm_size", type=int, help="HBM size in KB.")
    parser.add_argument(
        "--no_hbm",
        dest="has_hbm",
        action="store_false",
        help="If set, this flag tells he_prep there is no HBM in the target chip.",
    )
    parser.add_argument(
        "--suppress_comments",
        "--no_comments",
        dest="suppress_comments",
        action="store_true",
        help=("When enabled, no comments will be emitted on the output generated."),
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

    # Determine if using trace file based on trace_file argument
    p_args.using_trace_file = p_args.trace_file != ""

    # Set input_dir to trace_file directory if not provided and trace_file is set
    if p_args.input_dir == "" and p_args.trace_file:
        p_args.input_dir = os.path.dirname(p_args.trace_file)

    # Enforce only if use_trace_file is not set
    if not p_args.using_trace_file:
        if p_args.input_mem_file == "":
            parser.error("the following arguments are required: -im/--input_mem_file (unless --use_trace_file is set)")
        if not p_args.input_prefixes:
            parser.error("the following arguments are required: -ip/--input_prefixes (unless --use_trace_file is set)")
    else:
        # If using trace file, input_mem_file and input_prefixes are ignored
        if p_args.input_mem_file != "":
            warnings.warn("Ignoring input_mem_file argument because --use_trace_file is set.")
        if p_args.input_prefixes:
            warnings.warn("Ignoring input_prefixes argument because --use_trace_file is set.")

    return p_args


if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)

    args = parse_args()
    args.mem_spec_file = MemSpecConfig.initialize_mem_spec(module_dir, args.mem_spec_file)
    args.isa_spec_file = ISASpecConfig.initialize_isa_spec(module_dir, args.isa_spec_file)
    config = LinkerRunConfig(**vars(args))  # convert argsparser into a dictionary

    if args.verbose > 0:
        print(module_name)
        print()
        print("Run Configuration")
        print("=================")
        print(config)
        print("=================")
        print()

    main(config, sys.stdout if args.verbose > 1 else NullIO())

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
