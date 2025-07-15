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
    - KernelFiles: Structure for kernel files.

@par Functions:
    - main(run_config: LinkerRunConfig, verbose_stream=None): Executes the linking process using the provided configuration.
    - parse_args() -> argparse.Namespace: Parses command-line arguments for the linker script.

@par Usage:
    This script is intended to be run as a standalone program. It requires specific command-line arguments
    to specify input and output files and configuration options for the linking process.
"""
import argparse
import io
import os
import pathlib
import sys
import warnings
from typing import Any

import linker
from assembler.common import constants
from assembler.common import makeUniquePath
from assembler.common.counter import Counter
from assembler.common.run_config import RunConfig
from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info
from assembler.spec_config.mem_spec import MemSpecConfig
from assembler.spec_config.isa_spec import ISASpecConfig
from linker import loader
from linker.steps.variable_discovery import scan_variables, check_unused_variables
from linker.steps import program_linker
from linker.instructions import BaseInstruction
from linker.kern_trace import TraceInfo, KernelFiles, remap_dinstrs_vars


class NullIO:
    """
    @class NullIO
    @brief A class that provides a no-operation implementation of write and flush methods.
    """

    def write(self, *argts, **kwargs):
        """
        @brief A no-operation write method.
        """

    def flush(self):
        """
        @brief A no-operation flush method.
        """


class LinkerRunConfig(RunConfig):
    """
    @class LinkerRunConfig
    @brief Maintains the configuration data for the run.

    @fn as_dict
    @brief Returns the configuration as a dictionary.

    @return dict The configuration as a dictionary.
    """

    # Type annotations for class attributes
    input_prefixes: list[str]
    input_mem_file: str
    using_trace_file: bool
    trace_file: str
    input_dir: str
    output_dir: str
    output_prefix: str

    __initialized = False  # specifies whether static members have been initialized
    # contains the dictionary of all configuration items supported and their
    # default value (or None if no default)
    __default_config: dict[str, Any] = {}

    def __init__(self, **kwargs):
        """
        @brief Constructs a new LinkerRunConfig Object from input parameters.

        See base class constructor for more parameters.

        @param input_prefixes List of input prefixes, including full path. For an input prefix, linker will
            assume there are three files named `input_prefixes[i] + '.minst'`,
            `input_prefixes[i] + '.cinst'`, and `input_prefixes[i] + '.xinst'`.
            This list must not be empty.
        @param output_prefix Prefix for the output file names.
            Three files will be generated:
            `output_dir/output_prefix.minst`, `output_dir/output_prefix.cinst`, and
            `output_dir/output_prefix.xinst`.
            Output filenames cannot match input file names.
        @param input_mem_file Input memory file associated with the result kernel.
        @param output_dir OPTIONAL directory where to store all intermediate files and final output.
            This will be created if it doesn't exists.
            Defaults to current working directory.

        @exception TypeError A mandatory configuration value was missing.
        @exception ValueError At least, one of the arguments passed is invalid.
        """
        super().__init__(**kwargs)

        self.init_default_config()

        # class members based on configuration
        for config_name, default_value in self.__default_config.items():
            value = kwargs.get(config_name, default_value)
            if value is not None:
                setattr(self, config_name, value)
            else:
                if not hasattr(self, config_name):
                    setattr(self, config_name, default_value)
                    if getattr(self, config_name) is None:
                        raise TypeError(
                            f"Expected value for configuration `{config_name}`, but `None` received."
                        )

        # Fix file paths
        # E0203: Access to member 'input_mem_file' before its definition.
        # But it was defined in previous loop.
        if self.input_mem_file != "":  # pylint: disable=E0203
            self.input_mem_file = makeUniquePath(self.input_mem_file)
        if self.trace_file != "":
            self.trace_file = makeUniquePath(self.trace_file)

        self.output_dir = makeUniquePath(self.output_dir)
        self.input_dir = makeUniquePath(self.input_dir)

    @classmethod
    def init_default_config(cls):
        """
        @brief Initializes static members of the class.
        """
        if not cls.__initialized:
            cls.__default_config["input_prefixes"] = ""
            cls.__default_config["input_mem_file"] = ""
            cls.__default_config["using_trace_file"] = False
            cls.__default_config["trace_file"] = ""
            cls.__default_config["output_dir"] = os.getcwd()
            cls.__default_config["input_dir"] = os.getcwd()
            cls.__default_config["output_prefix"] = None

            cls.__initialized = True

    def __str__(self):
        """
        @brief Provides a string representation of the configuration.

        @return str The string for the configuration.
        """
        self_dict = self.as_dict()
        with io.StringIO() as retval_f:
            for key, value in self_dict.items():
                print(f"{key}: {value}", file=retval_f)
            retval = retval_f.getvalue()
        return retval

    def as_dict(self) -> dict:
        """
        @brief Provides the configuration as a dictionary.

        @return dict The configuration.
        """
        retval = super().as_dict()
        tmp_self_dict = vars(self)
        retval.update(
            {
                config_name: tmp_self_dict[config_name]
                for config_name in self.__default_config
            }
        )
        return retval


def prepare_output_files(run_config) -> KernelFiles:
    """
    @brief Prepares output file names and directories.

    @param run_config LinkerRunConfig object.
    @return KernelFiles Output file paths.
    """
    path_prefix = os.path.join(run_config.output_dir, run_config.output_prefix)
    pathlib.Path(run_config.output_dir).mkdir(exist_ok=True, parents=True)
    out_mem_file = (
        makeUniquePath(path_prefix + ".mem") if run_config.using_trace_file else None
    )
    return KernelFiles(
        directory=run_config.output_dir,
        prefix=run_config.output_prefix,
        minst=makeUniquePath(path_prefix + ".minst"),
        cinst=makeUniquePath(path_prefix + ".cinst"),
        xinst=makeUniquePath(path_prefix + ".xinst"),
        mem=out_mem_file,
    )


def prepare_input_files(run_config, output_files) -> list:
    """
    @brief Prepares input file names and checks for existence and conflicts.

    @param run_config LinkerRunConfig object.
    @param output_files KernelFiles for output.
    @return list List of KernelFiles for input.
    @exception FileNotFoundError If an input file does not exist.
    @exception RuntimeError If an input file matches an output file.
    """
    input_files = []
    for file_prefix in run_config.input_prefixes:
        print(f"ROCHA Processing input prefix: {file_prefix} on {run_config.input_dir}")
        path_prefix = os.path.join(run_config.input_dir, file_prefix)
        mem_file = (
            makeUniquePath(path_prefix + ".mem")
            if run_config.using_trace_file
            else None
        )
        kernel_files = KernelFiles(
            directory=run_config.input_dir,
            prefix=file_prefix,
            minst=makeUniquePath(path_prefix + ".minst"),
            cinst=makeUniquePath(path_prefix + ".cinst"),
            xinst=makeUniquePath(path_prefix + ".xinst"),
            mem=mem_file,
        )
        input_files.append(kernel_files)
        for input_filename in kernel_files[2:]:
            if input_filename:
                if not os.path.isfile(input_filename):
                    raise FileNotFoundError(input_filename)
                if input_filename in output_files:
                    raise RuntimeError(
                        f'Input files cannot match output files: "{input_filename}"'
                    )
    return input_files


def process_trace_file(trace_file):
    """
    @brief Process trace file to extract kernel operations and update input prefixes.

    @param run_config The configuration object.
    @param verbose_stream Stream for verbose output.
    @return dict Dictionary mapping kernel names to kernel operations.
    """
    trace_info = TraceInfo(trace_file)
    kernel_ops = trace_info.parse_kernel_ops()

    # Extract kernel prefixes from trace file
    kernel_ops_dict = {
        f"{kernel_op.expected_in_kern_file_name}_pisa.tw": kernel_op
        for kernel_op in kernel_ops
    }

    return kernel_ops_dict  # Only return the kernel_ops_dict


def process_kernel_dinstrs(input_files, kernel_ops_dict, verbose_stream):
    """
    @brief Process kernel DInstructions when using trace file.

    @param input_files List of input kernel files.
    @param kernel_ops_dict Dictionary mapping kernel names to kernel operations.
    @param verbose_stream Stream for verbose output.
    @return tuple Containing (kernel_dinstrs, remap_dicts) for further processing.
    """
    kernels_dinstrs = []
    remap_dicts = {}

    for kernel_files in input_files:
        print(f"ROCHA  Processing kernel: {kernel_files.prefix}", file=verbose_stream)

        kernel_dinstrs = loader.load_dinst_kernel_from_file(kernel_files.mem)
        # Remap dintrs' variables in kernel_dinstrs and return a mapping dict
        remap_dicts[kernel_files.prefix] = remap_dinstrs_vars(
            kernel_dinstrs, kernel_ops_dict[kernel_files.prefix]
        )

        kernels_dinstrs.append(kernel_dinstrs)

    # Concatenate all mem info objects into one
    kernel_dinstrs = program_linker.LinkedProgram.join_dinst_kernels(kernels_dinstrs)

    return kernel_dinstrs, remap_dicts


def initialize_memory_model(run_config, kernel_dinstrs=None, verbose_stream=None):
    """
    @brief Initialize the memory model based on configuration.

    @param run_config The configuration object.
    @param kernel_dinstrs Optional list of kernel DInstructions for trace file mode.
    @param verbose_stream Stream for verbose output.
    @return MemoryModel instance.
    """
    hbm_capacity_words = constants.convertBytes2Words(
        run_config.hbm_size * constants.Constants.KILOBYTE
    )

    # Parse memory information
    if kernel_dinstrs:
        mem_meta_info = mem_info.MemInfo.from_dinstrs(kernel_dinstrs)
    else:
        with open(run_config.input_mem_file, "r", encoding="utf-8") as mem_ifnum:
            mem_meta_info = mem_info.MemInfo.from_file_iter(mem_ifnum)

    # Initialize memory model
    print("Initializing linker memory model", file=verbose_stream)
    mem_model = linker.MemoryModel(hbm_capacity_words, mem_meta_info)
    print(f"  HBM capacity: {mem_model.hbm.capacity} words", file=verbose_stream)

    return mem_model


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
    kernel_ops_dict = {}
    remap_dicts = {}
    if run_config.using_trace_file:
        kernel_ops_dict = process_trace_file(run_config.trace_file)
        run_config.input_prefixes = list(kernel_ops_dict.keys())

        print(
            f"Found {len(run_config.input_prefixes)} kernels in trace file:",
            file=verbose_stream,
        )

        print("", file=verbose_stream)

    # Prepare input and output files
    output_files = prepare_output_files(run_config)
    input_files = prepare_input_files(run_config, output_files)

    # Reset counters
    Counter.reset()

    # Parse memory information and setup memory model
    print("Linking...", file=verbose_stream)
    print("", file=verbose_stream)
    print("Interpreting variable meta information...", file=verbose_stream)

    kernel_dinstrs = None
    if run_config.using_trace_file:
        kernel_dinstrs, remap_dicts = process_kernel_dinstrs(
            input_files, kernel_ops_dict, verbose_stream
        )

    # Initialize memory model
    mem_model = initialize_memory_model(run_config, kernel_dinstrs, verbose_stream)

    # Discover variables
    print("  Finding all program variables...", file=verbose_stream)
    print("  Scanning", file=verbose_stream)

    scan_variables(
        input_files=input_files,
        mem_model=mem_model,
        verbose_stream=verbose_stream,
        remap_dicts=remap_dicts,
    )

    check_unused_variables(mem_model)

    print(f"    Variables found: {len(mem_model.variables)}", file=verbose_stream)
    print("Linking started", file=verbose_stream)

    # Link kernels and generate outputs
    program_linker.LinkedProgram.link_kernels_to_files(
        input_files,
        output_files,
        mem_model,
        verbose_stream=verbose_stream,
        remap_dicts=remap_dicts,
    )

    # Write the memory model to the output file
    if run_config.using_trace_file:
        if output_files.mem is None:
            raise RuntimeError("Output memory file path is None")
        BaseInstruction.dump_instructions_to_file(kernel_dinstrs, output_files.mem)

    print("Output written to files:", file=verbose_stream)
    print("  ", output_files.minst, file=verbose_stream)
    print("  ", output_files.cinst, file=verbose_stream)
    print("  ", output_files.xinst, file=verbose_stream)
    if run_config.using_trace_file:
        print("  ", output_files.mem, file=verbose_stream)


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
            parser.error(
                "the following arguments are required: -im/--input_mem_file (unless --use_trace_file is set)"
            )
        if not p_args.input_prefixes:
            parser.error(
                "the following arguments are required: -ip/--input_prefixes (unless --use_trace_file is set)"
            )

    return p_args


if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)

    args = parse_args()
    args.mem_spec_file = MemSpecConfig.initialize_mem_spec(
        module_dir, args.mem_spec_file
    )
    args.isa_spec_file = ISASpecConfig.initialize_isa_spec(
        module_dir, args.isa_spec_file
    )
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
