# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to link kernels into a program."""

from assembler.instructions import cinst as ISACInst
from assembler.instructions import xinst as ISAXInst

from linker.instructions import cinst, minst, xinst
from linker.instructions.xinst.xinstruction import XInstruction
from linker.kern_trace.kernel_info import InstrAct


class XStoreMoveMapEntry:
    """
    @brief Represents a mapping entry for an XStore instruction and its associated Move instruction.
    """

    def __init__(self, reg_name: str, kernel_idx: int, xinstrs_n_xstore_idx: tuple[list, int], action: InstrAct):
        self._reg_name: str = reg_name
        self._xstore_kernel_idx: int = kernel_idx
        self._xinstrs_n_xstore_idx: tuple[list, int] = xinstrs_n_xstore_idx
        self._xinstrs_n_move_idx: tuple[list, int] = ([], -1)  # to be filled later
        self._action = action

    @property
    def reg_name(self) -> str:
        """@brief Gets the register name associated with the instruction."""
        return self._reg_name

    @property
    def xstore_kernel_idx(self) -> int:
        """@brief Gets the kernel index where the XStore instruction is located."""
        return self._xstore_kernel_idx

    @property
    def xstore_instr(self) -> XInstruction:
        """@brief Gets the XStore instruction."""
        xinstrs, idx = self._xinstrs_n_xstore_idx
        return xinstrs[idx]

    def replace_xstore_with_nop(self):
        """@brief Replaces the XStore instruction with a Nop instruction."""

        if self._xinstrs_n_move_idx[1] == -1:
            raise RuntimeError("Move instruction index not set. Cannot replace Move with original register.")

        xinstrs, idx = self._xinstrs_n_xstore_idx
        self.move_instr.source = xinstrs[idx].source  # Set original register in Move instruction
        xinstrs[idx] = xinst.Nop(
            [f"F{xinstrs[idx].bundle}", str(idx), xinst.Nop.name, str(3)],
            comment=f"Replaced XStore for {xinstrs[idx].source} with Nop; {xinstrs[idx].comment}",
        )

    def replace_xstore_with_move(self, reg_name: str):
        """@brief Replaces the XStore instruction with a Move instruction."""
        xinstrs, idx = self._xinstrs_n_xstore_idx
        xinstrs[idx] = xinst.Move(
            [f"F{xinstrs[idx].bundle}", str(idx), xinst.Move.name, reg_name, xinstrs[idx].source],
            comment=f"Replaced XStore for {xinstrs[idx].source} with Move to {reg_name}",
        )

    @property
    def move_instr(self) -> XInstruction:
        """@brief Gets the Move instruction."""
        xinstrs, idx = self._xinstrs_n_move_idx
        return xinstrs[idx]

    @move_instr.setter
    def move_instr(self, xinstrs_n_move_idx: tuple[list, int]):
        """@brief Sets the Move instruction."""
        self._xinstrs_n_move_idx = xinstrs_n_move_idx

    @property
    def action(self) -> InstrAct:
        """@brief Gets the action associated with the instruction."""
        return self._action

    @action.setter
    def action(self, action: InstrAct):
        """@brief Sets the action associated with the instruction."""
        self._action = action


def get_instruction_tp(cinstr) -> int:
    """
    @brief Get the latency for different instruction types.

    @param cinstr The instruction to calculate latency for.
    @return int The latency value.
    """
    if isinstance(cinstr, cinst.BLoad):
        return ISACInst.BLoad.get_throughput()
    if isinstance(cinstr, cinst.BOnes):
        return ISACInst.BOnes.get_throughput()
    if isinstance(cinstr, cinst.NLoad):
        return ISACInst.NLoad.get_throughput()
    if isinstance(cinstr, cinst.XInstFetch):
        return ISACInst.XInstFetch.get_throughput()
    if isinstance(cinstr, cinst.CLoad):
        return ISACInst.CLoad.get_throughput()
    return 0


def get_instruction_lat(xinstr) -> int:
    """
    @brief Get the latency for different instruction types.

    @param xinstr The instruction to calculate latency for.
    @return int The latency value.
    """
    # Map xinstr classes to their corresponding assembler latency getter.
    _lat_getters = {
        xinst.Add: ISAXInst.Add.get_latency,
        xinst.Sub: ISAXInst.Sub.get_latency,
        xinst.Mul: ISAXInst.Mul.get_latency,
        xinst.Muli: ISAXInst.Muli.get_latency,
        xinst.Mac: ISAXInst.Mac.get_latency,
        xinst.Maci: ISAXInst.Maci.get_latency,
        xinst.INTT: ISAXInst.iNTT.get_latency,
        xinst.NTT: ISAXInst.NTT.get_latency,
        xinst.TwNTT: ISAXInst.twNTT.get_latency,
        xinst.TwiNTT: ISAXInst.twiNTT.get_latency,
        xinst.XStore: ISAXInst.XStore.get_latency,
        xinst.Move: ISAXInst.Move.get_latency,
        xinst.Nop: ISAXInst.Nop.get_latency,
        xinst.RShuffle: ISAXInst.rShuffle.get_latency,
        xinst.Exit: ISAXInst.Exit.get_latency,
    }

    for cls, getter in _lat_getters.items():
        if isinstance(xinstr, cls):
            try:
                return getter()
            except (TypeError, AttributeError, ValueError):
                return 0
    return 0


def proc_seq_bloads(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, start_idx):
    """
    @brief Process consecutive BLoad instructions and mark duplicates for skipping.

    @param kernel_cinstrs List of CInstructions.
    @param kernel_cinstrs_map Map of CInstructions with actions.
    @param cinst_in_var_tracker Dictionary tracking loaded variables.
    @param start_idx Starting index for processing.
    @return int The last processed index.
    """
    idx = start_idx
    tp = 0
    # Look ahead and process all consecutive BLoad instructions
    while idx < len(kernel_cinstrs) and isinstance(kernel_cinstrs[idx], cinst.BLoad):
        if kernel_cinstrs[idx].var_name in cinst_in_var_tracker:
            kernel_cinstrs_map[idx].action = InstrAct.SKIP
        else:
            tp += ISACInst.BLoad.get_throughput()
        idx += 1

    # Adjust index since the calling loop will increment it again
    return (tp, idx - 1)


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


def search_cinstrs_back(cinstrs_map: list, idx: int, reg_name: str) -> str:
    """
    @brief Searches for a CInstruction that writes to a specific register.

    This method is used to find the instruction associated with a given register
    in the CInsts of a kernel.

    @param cinstrs_map Map with CInstructions to search.
    @param idx Index to start searching from (inclusive, backwards).
    @param reg_name The register name to search for.

    @return str The variable name associated with the register.
    """
    # Traverse backwards from idx, including idx
    if idx < 0 or idx >= len(cinstrs_map):
        raise IndexError(f"Index {idx} is out of bounds for cinstrs_map of length {len(cinstrs_map)}.")

    for i in range(idx, -1, -1):
        cinstr = cinstrs_map[i].cinstr
        if isinstance(cinstr, cinst.CLoad) and cinstr.register == reg_name:
            return cinstr.var_name

    return ""  # Not found
