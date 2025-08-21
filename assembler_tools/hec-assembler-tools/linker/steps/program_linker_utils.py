# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to link kernels into a program."""

from assembler.instructions import cinst as ISACInst

from linker.instructions import cinst, minst
from linker.kern_trace.kernel_info import InstrAct


def calculate_instruction_latency_adjustment(cinstr) -> int:
    """
    @brief Calculate the latency adjustment for different instruction types.

    @param cinstr The instruction to calculate latency for.
    @return int The latency adjustment value.
    """
    if isinstance(cinstr, cinst.CLoad):
        return ISACInst.CLoad.get_latency()
    if isinstance(cinstr, cinst.BLoad):
        return ISACInst.BLoad.get_latency()
    if isinstance(cinstr, cinst.BOnes):
        return ISACInst.BOnes.get_latency()
    return 0


def process_bload_instructions(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, start_idx):
    """
    @brief Process consecutive BLoad instructions and mark duplicates for skipping.

    @param kernel_cinstrs List of CInstructions.
    @param kernel_cinstrs_map Map of CInstructions with actions.
    @param cinst_in_var_tracker Dictionary tracking loaded variables.
    @param start_idx Starting index for processing.
    @return int The last processed index.
    """
    idx = start_idx

    # Look ahead and process all consecutive BLoad instructions
    while idx < len(kernel_cinstrs) and isinstance(kernel_cinstrs[idx], cinst.BLoad):
        if kernel_cinstrs[idx].var_name in cinst_in_var_tracker:
            kernel_cinstrs_map[idx].action = InstrAct.SKIP
        idx += 1

    # Adjust index since the calling loop will increment it again
    return idx - 1


def remove_csyncm(kernel_cinstrs, kernel_cinstrs_map, idx):
    """
    @brief Remove instruction at target idx if that is a CSyncm.

    @param kernel_cinstrs List of CInstructions.
    @param kernel_cinstrs_map Map of CInstructions with actions.
    @param idx Index of the instruction to check.

    @return tuple (adjust_idx, adjust_cycles) Adjustments for index and cycles.
    """
    adjust_idx = 0
    adjust_cycles = 0

    # Check if target instruction exists and is CSyncm
    if 0 <= idx < len(kernel_cinstrs):
        target_cinstr = kernel_cinstrs[idx]
        if isinstance(target_cinstr, cinst.CSyncm):
            kernel_cinstrs_map[idx].action = InstrAct.SKIP
            adjust_cycles = ISACInst.CSyncm.get_throughput()
            adjust_idx = -1

    return adjust_idx, adjust_cycles


def search_minstrs_back(minstrs_map: list, idx: int, spad_address: int) -> int:
    """
    @brief Searches for an MLoad based on its SPAD address.

    This method is used to find the instruction associated with a given SPAD address
    in the MInsts of a kernel.

    @param minstrs_map Map with MInstructions to search.
    @param idx Index to start searching from (inclusive, backwards).
    @param spad_address The SPAD address to search for.

    @return int Index for the MLoad instruction associated with the SPAD address.
    """
    # Traverse backwards from idx, including idx
    if idx < 0 or idx >= len(minstrs_map):
        raise IndexError(f"Index {idx} is out of bounds for minstrs_map of length {len(minstrs_map)}.")

    for i in range(idx, -1, -1):
        minstr = minstrs_map[i].minstr
        if isinstance(minstr, minst.MLoad) and minstrs_map[i].spad_addr == spad_address:
            return i

    raise RuntimeError(f"Could not find MLoad with SPAD address {spad_address} in kernel MInsts.")


def search_minstrs_forward(minstrs_map: list, idx: int, spad_address: int) -> int:
    """
    @brief Searches for an MStore/MLoad based on its SPAD address

    This method is used to find the instruction associated with a given SPAD address
    in the MInsts of a kernel.

    @param minstrs_map Map with MInstructions to search.
    @param idx Index to start searching from (inclusive, forwards).
    @param spad_address The SPAD address to search for.

    @return int Index for the MInstruction associated with the SPAD address.
    """
    # Traverse forwards from idx, including idx
    for i in range(idx, len(minstrs_map)):
        minstr = minstrs_map[i].minstr
        if isinstance(minstr, (minst.MStore, minst.MLoad)) and minstrs_map[i].spad_addr == spad_address:
            return i

    raise RuntimeError(f"Could not find MStore with SPAD address {spad_address} in kernel MInsts.")
