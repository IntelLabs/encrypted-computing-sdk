# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief This module implements the DKeyGen instruction for key generation operations.
"""

from assembler.memory_model.mem_info import MemInfo

from .dinstruction import DInstruction


class Instruction(DInstruction):
    """
    @brief Encapsulates a `dkeygen` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction.
        """
        return MemInfo.Const.Keyword.KEYGEN
