# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief This module provides functionality to discover variable names in MInstructions and CInstructions.
"""
from typing import Optional, TextIO, List
from assembler.memory_model.variable import Variable
from assembler.memory_model import MemoryModel
from assembler.common.config import GlobalConfig
from linker.instructions import minst, cinst
from linker.instructions.minst.minstruction import MInstruction
from linker.instructions.cinst.cinstruction import CInstruction
from linker.kern_trace import KernelInfo, remap_m_c_instrs_vars
from linker.loader import Loader


def discover_variables_spad(cinstrs: list):
    """
    @brief Finds Variable names used in a list of CInstructions.

    @param cinstrs List of CInstructions where to find variable names.
    @throws TypeError If an item in the list is not a valid CInstruction.
    @throws RuntimeError If an invalid Variable name is detected in a CInstruction.
    @return Yields an iterable over variable names identified in the listing
            of CInstructions specified.
    """
    for idx, cinstr in enumerate(cinstrs):
        if not isinstance(cinstr, CInstruction):
            raise TypeError(
                f"Item {idx} in list of CInstructions is not a valid CInstruction."
            )
        retval = None
        # TODO: Implement variable counting for CInst
        ###############
        # Raise NotImplementedError("Implement variable counting for CInst")
        if isinstance(cinstr, (cinst.BLoad, cinst.CLoad, cinst.BOnes, cinst.NLoad)):
            retval = cinstr.source
        elif isinstance(cinstr, cinst.CStore):
            retval = cinstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(
                    f'Invalid Variable name "{retval}" detected in instruction "{idx}, {cinstr.to_line()}"'
                )
            yield retval


def discover_variables(minstrs: list):
    """
    @brief Finds variable names used in a list of MInstructions.

    @param minstrs List of MInstructions where to find variable names.
    @throws TypeError If an item in the list is not a valid MInstruction.
    @throws RuntimeError If an invalid variable name is detected in an MInstruction.
    @return Yields an iterable over variable names identified in the listing
            of MInstructions specified.
    """
    for idx, minstr in enumerate(minstrs):
        if not isinstance(minstr, MInstruction):
            raise TypeError(
                f"Item {idx} in list of MInstructions is not a valid MInstruction."
            )
        retval = None
        if isinstance(minstr, minst.MLoad):
            retval = minstr.source
        elif isinstance(minstr, minst.MStore):
            retval = minstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(
                    f'Invalid Variable name "{retval}" detected in instruction "{idx}, {minstr.to_line()}"'
                )
            yield retval


def scan_variables(
    kernels_info: List[KernelInfo],
    mem_model: MemoryModel,
    verbose_stream: Optional[TextIO] = None,
):
    """
    @brief Scans input files for variables and adds them to the memory model.

    @param kernels_info List of KernelInfo for input.
    @param mem_model Memory model to update.
    @param verbose_stream Stream for verbose output.
    """
    for idx, kernel_info in enumerate(kernels_info):

        if not GlobalConfig.hasHBM:
            if verbose_stream:
                print(
                    f"    {idx + 1}/{len(kernels_info)}",
                    kernel_info.cinst,
                    file=verbose_stream,
                )
            kernel_cinstrs = Loader.load_cinst_kernel_from_file(kernel_info.cinst)
            remap_m_c_instrs_vars(kernel_cinstrs, kernel_info.remap_dict)
            for var_name in discover_variables_spad(kernel_cinstrs):
                mem_model.add_variable(var_name)
        else:
            if verbose_stream:
                print(
                    f"    {idx + 1}/{len(kernels_info)}",
                    kernel_info.minst,
                    file=verbose_stream,
                )
            kernel_minstrs = Loader.load_minst_kernel_from_file(kernel_info.minst)
            remap_m_c_instrs_vars(kernel_minstrs, kernel_info.remap_dict)
            for var_name in discover_variables(kernel_minstrs):
                mem_model.add_variable(var_name)


def check_unused_variables(mem_model):
    """
    @brief Checks for unused variables in the memory model and raises an error if found.

    @param mem_model Memory model to check.
    @exception RuntimeError If an unused variable is found.
    """
    for var_name in mem_model.mem_info_vars:
        if var_name not in mem_model.variables:
            if GlobalConfig.hasHBM or var_name not in mem_model.mem_info_meta:
                raise RuntimeError(
                    f'Unused variable from input mem file: "{var_name}" not in memory model.'
                )
