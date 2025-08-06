# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to create and manage data instructions"""

from typing import Optional

from assembler.instructions import tokenize_from_line

from . import dinstruction, dkeygen, dload, dstore

DLoad = dload.Instruction
DStore = dstore.Instruction
DKeyGen = dkeygen.Instruction


def factory() -> set:
    """
    @brief Creates a set of all DInstruction classes.

    @return A set containing all DInstruction classes.
    """
    return {DLoad, DStore, DKeyGen}


def create_from_mem_line(line: str) -> dinstruction.DInstruction:
    """
    @brief Parses an data instruction from a line of the memory map.

    @param line Line of text from which to parse an instruction.
    @return The parsed DInstruction object, or None if no object could be
            parsed from the specified input line.
    @throws RuntimeError If no valid instruction is found or if there's an error parsing the memory map line.
    """
    retval: dinstruction.DInstruction | None = None
    tokens, comment = tokenize_from_line(line)
    for instr_type in factory():
        try:
            retval = instr_type(tokens, comment)
        except ValueError:
            retval = None
        if retval:
            break

    if not retval:
        raise RuntimeError(f'No valid instruction found for line "{line}"')

    return retval
