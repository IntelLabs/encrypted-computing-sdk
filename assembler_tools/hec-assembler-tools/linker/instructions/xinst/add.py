# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the add X-instruction which performs element-wise polynomial addition."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `add` XInstruction.

    This instruction adds two polynomials stored in the register file and
    stores the result in a register.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_add.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `add` instruction requires 7 tokens:
        F<bundle_idx: uint>, <info: str>, add, <dst: str>, <src0: str>, <src1: str>, <res: uint>

        @return The number of tokens, which is 7.
        """
        return 7

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "add".
        """
        return "add"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `add` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
