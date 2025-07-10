# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the mstore M-instruction which stores data from scratchpad to memory."""

from .minstruction import MInstruction


class Instruction(MInstruction):
    """
    @brief Encapsulates an `mstore` MInstruction.

    This instruction stores a single polynomial residue from scratchpad to local memory.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mstore.md

    Properties:
        dest: Gets or sets the name of the destination.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `mstore` instruction requires 4 tokens:
        <line: uint>, mstore, <dst_var: str>, <src: uint>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "mstore".
        """
        return "mstore"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `mstore` MInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def dest(self) -> str:
        """
        @brief Gets the name of the destination.

        This is a Variable name when loaded. Should be set to HBM address to write back.

        @return The name of the destination.
        """
        return self.tokens[2]

    @dest.setter
    def dest(self, value: str):
        """
        @brief Sets the name of the destination.

        @param value The name of the destination to set.
        """
        self.tokens[2] = value
