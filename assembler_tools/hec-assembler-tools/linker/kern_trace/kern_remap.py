# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for remapping kernel variables in DINST files."""

import re

from linker.instructions import cinst, minst
from linker.instructions.cinst.cinstruction import CInstruction
from linker.instructions.dinst.dinstruction import DInstruction
from linker.instructions.minst.minstruction import MInstruction
from linker.kern_trace.kernel_op import KernelOp


def remap_dinstrs_vars(kernel_dinstrs: list[DInstruction], kernel_op: KernelOp) -> dict[str, str]:
    """
    @brief Remaps variable names in DInstructions based on KernelOp variables.

    For each variable name in the kernel_dinstrs:
    1. Extracts a prefix separated by '_'
    2. Ignores variables with prefixes 'ntt', 'intt', 'ones', 'ipsi', 'psi', 'rlk' or 'twid'
    3. Extracts a number from the prefix (digits after text)
    4. Uses this number as an index into the sorted list of KernelOp variables
    5. Replaces the dinstr var name prefix with the value obtained by the index

    @param kernel_dinstrs: List of DInstruction objects to process
    @param kernel_op: KernelOp containing variables to use for remapping
    @return: Dictionary mapping old variable names to new variable names
    """

    # Sort kernel_op variables by label
    sorted_kern_vars = sorted(kernel_op.kern_vars, key=lambda x: x.label)

    # Dictionary to store mapping of old var names to new var names
    var_mapping = {}

    # Process each DInstruction
    for dinstr in kernel_dinstrs:
        # Split the variable name by '_' to get the prefix
        try:
            prefix, rest = dinstr.var.split("_", 1)
        except ValueError as e:
            raise ValueError(f"Unexpected format: variable name '{dinstr.var}' does not contain items to split by '_': {e}") from e

        # Skip if prefix is not 'ct' or 'pt'
        if not (prefix.lower().startswith("ct") or prefix.lower().startswith("pt")):
            continue

        # Extract number from prefix (digits after text)
        match = re.search(r"([a-zA-Z]+)(\d+)", prefix)

        if not match:
            raise ValueError(f"Unexpected format: variable prefix '{prefix}' does not contain a number after text.")

        number_part = int(match.group(2))

        # Use number as index if it's valid
        try:
            # Replace prefix with kernel variable label
            kern_var = sorted_kern_vars[number_part]
        except IndexError as exc:
            raise IndexError(
                f"Number part {number_part} from prefix '{prefix}' is out of range [0, {len(sorted_kern_vars)-1}]"
                "for the KernelOp variables"
            ) from exc

        old_var = dinstr.var
        new_var = f"{kern_var.label}_{rest}"
        dinstr.var = new_var
        var_mapping[old_var] = new_var

    return var_mapping


def remap_m_c_instrs_vars(kernel_instrs: list, remap_dict: dict[str, str]) -> None:
    """
    @brief Remaps variable names in M or C Instructions based on a provided remap dictionary.

    This function updates the variable names in each Instruction by replacing them
    with their corresponding values from the remap dictionary.

    @param kernel_instrs: List of M or M Instruction objects to process
    @param remap_dict: Dictionary mapping old variable names to new variable names
    """
    if remap_dict:
        for instr in kernel_instrs:
            if not isinstance(instr, MInstruction | CInstruction):
                raise TypeError(f"Item {instr} is not a valid M or C Instruction.")

            if isinstance(instr, minst.MLoad | cinst.BLoad | cinst.CLoad | cinst.BOnes | cinst.NLoad):
                if instr.source in remap_dict:
                    instr.comment = instr.comment.replace(instr.source, remap_dict[instr.source])
                    instr.source = remap_dict[instr.source]
            elif isinstance(instr, minst.MStore | cinst.CStore):
                if instr.dest in remap_dict:
                    instr.comment = instr.comment.replace(instr.dest, remap_dict[instr.dest])
                    instr.dest = remap_dict[instr.dest]
