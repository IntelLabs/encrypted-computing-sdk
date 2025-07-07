# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""This module provides functionality to create and manage data instructions"""

from typing import Optional

from assembler.instructions import tokenize_from_line
from assembler.memory_model.mem_info import MemInfo
from . import dload, dstore, dkeygen
from . import dinstruction

DLoad = dload.Instruction
DStore = dstore.Instruction
DKeyGen = dkeygen.Instruction


def factory() -> set:
    """
    Creates a set of all DInstruction classes.

    Returns:
        set: A set containing all DInstruction classes.
    """
    return {DLoad, DStore, DKeyGen}


def create_from_mem_line(line: str) -> dinstruction.DInstruction:
    """
    Parses an data instruction from a line of the memory map.

    Parameters:
        line (str): Line of text from which to parse an instruction.

    Returns:
        DInstruction or None: The parsed DInstruction object, or None if no object could be
        parsed from the specified input line.
    """
    print(f"ROCHA: create_from_mem_line {line}")
    retval: Optional[dinstruction.DInstruction] = None
    tokens, comment = tokenize_from_line(line)
    for instr_type in factory():
        try:
            retval = instr_type(tokens, comment)
            print(f"ROCHA: {instr_type.__name__} {tokens} {retval}")
        except ValueError:
            retval = None
        if retval:
            break

    if not retval:
        raise RuntimeError(f'No valid instruction found for line "{line}"')

    try:
        miv, _ = MemInfo.get_meminfo_var_from_tokens(tokens)
    except RuntimeError as e:
        raise RuntimeError(f'Error parsing memory map line "{line}"') from e

    miv_dict = miv.as_dict()
    retval.var = miv_dict["var_name"]
    retval.address = miv_dict["hbm_address"]

    return retval
