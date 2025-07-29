# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the bexit X-instruction which terminates execution of an instruction bundle."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `bexit` XInstruction.

    This instruction terminates execution of an instruction bundle.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_exit.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `bexit` instruction requires 3 tokens:
        F<bundle_idx: uint>, <info: str>, bexit

        @return The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "bexit".
        """
        return "bexit"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `bexit` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
