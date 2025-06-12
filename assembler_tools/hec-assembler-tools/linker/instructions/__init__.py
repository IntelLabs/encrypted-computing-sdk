# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from assembler.instructions import tokenize_from_line
from linker.instructions.instruction import BaseInstruction


def fromStrLine(line: str, factory) -> BaseInstruction:
    """
    Parses an instruction from a line of text.

    Parameters:
        line (str): Line of text from which to parse an instruction.

    Returns:
        BaseInstruction or None: The parsed BaseInstruction object, or None if no object could be
        parsed from the specified input line.
    """
    retval = None
    tokens, comment = tokenize_from_line(line)
    for instr_type in factory:
        try:
            retval = instr_type(tokens, comment)
        except:
            retval = None
        if retval:
            break

    return retval
