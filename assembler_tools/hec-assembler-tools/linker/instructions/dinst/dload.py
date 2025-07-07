# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
This module implements the DLoad instruction for loading data from memory.

The DLoad instruction is used to load data from specified memory locations
during the assembly process.
"""

from assembler.memory_model.mem_info import MemInfo
from .dinstruction import DInstruction


class Instruction(DInstruction):
    """
    Encapsulates a `dload` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction.
        """
        return MemInfo.Const.Keyword.LOAD

    @property
    def tokens(self) -> list:
        """
        Gets the list of tokens for the instruction.

        Returns:
            list: The list of tokens.
        """
        return [self.name, self._tokens[1], str(self.address)] + self._tokens[3:]
