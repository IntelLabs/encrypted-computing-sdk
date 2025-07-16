# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file he_link_utils.py
@brief Utility functions for the he_link module
"""
import os
import pathlib

import linker
from assembler.common import constants
from assembler.common import makeUniquePath
from assembler.memory_model import mem_info
from linker import loader
from linker.steps import program_linker
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


def process_kernel_dinstrs(kernels_files, kernel_ops_dict, verbose_stream):
    """
    @brief Process kernel DInstructions when using trace file.

    @param kernels_files List of input KernelFiles.
    @param kernel_ops_dict Dictionary mapping kernel names to kernel operations.
    @param verbose_stream Stream for verbose output.
    @return tuple Containing (kernel_dinstrs, remap_dicts) for further processing.
    """
    kernels_dinstrs = []
    remap_dicts = {}

    for kernel_files in kernels_files:
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
