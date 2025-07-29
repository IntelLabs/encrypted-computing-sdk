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
from linker.kern_trace import KernelInfo, remap_dinstrs_vars


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


def prepare_output_files(run_config) -> KernelInfo:
    """
    @brief Prepares output file names and directories.

    @param run_config LinkerRunConfig object.
    @return KernelInfo with output file paths.
    """
    path_prefix = os.path.join(run_config.output_dir, run_config.output_prefix)
    pathlib.Path(run_config.output_dir).mkdir(exist_ok=True, parents=True)
    out_mem_file = (
        makeUniquePath(path_prefix + ".mem") if run_config.using_trace_file else None
    )
    return KernelInfo(
        {
            "directory": run_config.output_dir,
            "prefix": run_config.output_prefix,
            "minst": makeUniquePath(path_prefix + ".minst"),
            "cinst": makeUniquePath(path_prefix + ".cinst"),
            "xinst": makeUniquePath(path_prefix + ".xinst"),
            "mem": out_mem_file,
        }
    )


def prepare_input_files(run_config, output_files) -> list:
    """
    @brief Prepares input file names and checks for existence and conflicts.

    @param run_config LinkerRunConfig object.
    @param output_files KernelInfo for output.
    @return list List of KernelInfo for input.
    @exception FileNotFoundError If an input file does not exist.
    @exception RuntimeError If an input file matches an output file.
    """
    input_files = []
    for file_prefix in run_config.input_prefixes:
        path_prefix = os.path.join(run_config.input_dir, file_prefix)
        mem_file = (
            makeUniquePath(path_prefix + ".mem")
            if run_config.using_trace_file
            else None
        )
        kernel_info = KernelInfo(
            {
                "directory": run_config.input_dir,
                "prefix": file_prefix,
                "minst": makeUniquePath(path_prefix + ".minst"),
                "cinst": makeUniquePath(path_prefix + ".cinst"),
                "xinst": makeUniquePath(path_prefix + ".xinst"),
                "mem": mem_file,
            }
        )
        input_files.append(kernel_info)
        for input_filename in kernel_info.files:
            if not os.path.isfile(input_filename):
                raise FileNotFoundError(input_filename)
            if input_filename in output_files.files:
                raise RuntimeError(
                    f'Input files cannot match output files: "{input_filename}"'
                )
    return input_files


def update_input_prefixes(kernel_ops, run_config):
    """
    @brief Update input prefixes in run_config.

    @param kernel_ops List of kernel operations to extract prefixes from.
    @param run_config LinkerRunConfig object to update with input prefixes.
    """
    # Extract kernel prefixes and create list of (prefix, operation) tuples
    prefixes = []
    for kernel_op in kernel_ops:
        prefix = f"{kernel_op.expected_in_kern_file_name}_pisa.tw"
        prefixes.append(prefix)

    # Update input_prefixes in run_config
    run_config.input_prefixes = prefixes


def remap_vars(
    kernels_info: list[KernelInfo], kernels_dinstrs, kernel_ops, verbose_stream
):
    """
    @brief Process kernel DInstructions to remap variables based on kernel operations
    and update KernelInfo with remap_dict.

    @param kernels_info List of input KernelInfo.
    @param kernels_dinstrs List of kernel DInstructions.
    @param kernel_ops List of kernel operations.
    @param verbose_stream Stream for verbose output.
    """
    assert len(kernels_info) == len(
        kernel_ops
    ), "Number of kernels_files must match number of kernel operations."
    assert len(kernels_dinstrs) == len(
        kernel_ops
    ), "Number of kernel_dinstrs must match number of kernel operations."

    for kernel_info, kernel_op, kernel_dinstrs in zip(
        kernels_info, kernel_ops, kernels_dinstrs
    ):
        print(f"\tProcessing kernel: {kernel_info.prefix}", file=verbose_stream)

        expected_prefix = f"{kernel_op.expected_in_kern_file_name}_pisa.tw"
        assert expected_prefix in kernel_info.prefix, (
            f"Kernel operation prefix {expected_prefix} does not match "
            f"kernel file prefix {kernel_info.prefix}"
        )

        # Remap dintrs' variables in kernel_dinstrs and return a mapping dict
        var_map = remap_dinstrs_vars(kernel_dinstrs, kernel_op)
        kernel_info.remap_dict = var_map


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
