# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to create instruction objects from a line of text."""

from assembler.instructions import tokenize_from_line

from linker.instructions.instruction import BaseInstruction


def create_from_str_line(line: str, factory) -> BaseInstruction | None:
    """
    @brief Parses an instruction from a line of text.

    @param line Line of text from which to parse an instruction.
    @param factory Factory function or collection to create instruction objects.
    @return The parsed BaseInstruction object, or None if no object could be
            parsed from the specified input line.
    """
    retval = None
    tokens, comment = tokenize_from_line(line)
    for instr_type in factory:
        try:
            retval = instr_type(tokens, comment)
        except (TypeError, ValueError, AttributeError):
            retval = None
        if retval:
            break

    return retval
