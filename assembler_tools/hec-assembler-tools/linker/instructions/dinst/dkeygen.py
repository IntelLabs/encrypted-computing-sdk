# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
This module implements the DKeyGen instruction for key generation operations.
"""

from assembler.memory_model.mem_info import MemInfo

from .dinstruction import DInstruction


class Instruction(DInstruction):
    """
    Encapsulates a `dkeygen` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction.
        """
        return MemInfo.Const.Keyword.KEYGEN
