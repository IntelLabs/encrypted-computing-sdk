# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the mload M-instruction which loads data from memory to scratchpad."""

from .minstruction import MInstruction


class Instruction(MInstruction):
    """
    @brief Encapsulates an `mload` MInstruction.

    This instruction loads a single polynomial residue from local memory to scratchpad.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mload.md

    Properties:
        source: Gets or sets the name of the source.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `mload` instruction requires 4 tokens:
        <line: uint>, mload, <dst: uint>, <src_var: str>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "mload".
        """
        return "mload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `mload` MInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def source(self) -> str:
        """
        @brief Gets the name of the source.

        This is a Variable name when loaded. Should be set to HBM address to write back.

        @return The name of the source.
        """
        return self.tokens[3]

    @source.setter
    def source(self, value: str):
        """
        @brief Sets the name of the source.

        @param value The name of the source to set.
        """
        self.tokens[3] = value
