# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the move X-instruction which copies data from one register to another."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates a `move` XInstruction.

    This instruction copies data from one register to a different one.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_move.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `move` instruction requires 5 tokens:
        F<bundle_idx: uint>, <info: str>, move, <dst: str>, <src: str>

        @return The number of tokens, which is 5.
        """
        return 5

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "move".
        """
        return "move"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `move` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def source(self) -> str:
        """
        @brief Retrieves the source register of the instruction.
        @return The source register as a string.
        """
        return self.tokens[4]

    @source.setter
    def source(self, value: str):
        """
        @brief Sets the source register of the instruction.
        @param value The new source register as a string.
        """
        self.tokens[4] = value

    @property
    def dest(self) -> str:
        """
        @brief Retrieves the destination register of the instruction.
        @return The destination register as a string.
        """
        return self.tokens[3]

    @dest.setter
    def dest(self, value: str):
        """
        @brief Sets the destination register of the instruction.
        @param value The new destination register as a string.
        """
        self.tokens[3] = value
