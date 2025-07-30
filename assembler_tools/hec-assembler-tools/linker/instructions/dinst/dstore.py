# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief This module implements the DStore instruction for storing data to memory.

The DStore instruction is used to store data to specified memory locations
during the assembly process.
"""

from assembler.memory_model.mem_info import MemInfo

from .dinstruction import DInstruction


class Instruction(DInstruction):
    """
    @brief Encapsulates a `dstore` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        @return The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction.
        """
        return MemInfo.Const.Keyword.STORE

    @property
    def tokens(self) -> list:
        """
        @brief Gets the list of tokens for the instruction.

        @return The list of tokens.
        """
        return [self.name, self.var, str(self.address)] + self._tokens[3:]
