# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the cexit C-instruction which terminates the control flow execution."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `cexit` CInstruction.

    This instruction terminates execution of a HERACLES program.

    For more information, check the `cexit` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cexit.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `cexit` instruction requires 2 tokens:
        <line: uint>, cexit

        @return The number of tokens, which is 2.
        """
        return 2

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "cexit".
        """
        return "cexit"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `cexit` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
