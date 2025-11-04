# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the mul X-instruction which performs element-wise polynomial multiplication."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates a `mul` XInstruction.

    This instruction performs element-wise polynomial multiplication.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_mul.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `mul` instruction requires 7 tokens:
        F<bundle_idx: uint>, <info: str>, mul, <dst: str>, <src0: str>, <src1: str>, <res: uint>

        @return The number of tokens, which is 7.
        """
        return 7

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "mul".
        """
        return "mul"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `mul` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

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
