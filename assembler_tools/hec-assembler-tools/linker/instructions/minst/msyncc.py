# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the msyncc M-instruction which synchronizes with the control flow."""

from .minstruction import MInstruction


class Instruction(MInstruction):
    """
    @brief Encapsulates an `msyncc` MInstruction.

    Wait instruction similar to a barrier that stalls the execution of the MINST
    queue until the specified instruction from the CINST queue has completed.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_msyncc.md

    Properties:
        target: Gets or sets the target CInst.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `msyncc` instruction requires 3 tokens:
        <line: uint>, msyncc, <target: uint>

        @return The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "msyncc".
        """
        return "msyncc"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `msyncc` MInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def target(self) -> int:
        """
        @brief Gets the target CInst.

        @return The target CInst.
        """
        return int(self.tokens[2])

    @target.setter
    def target(self, value: int):
        """
        @brief Sets the target CInst.

        @param value The target CInst to set.
        @throws ValueError If the value is negative.
        """
        if value < 0:
            raise ValueError(
                f"`value`: expected non-negative target, but {value} received."
            )
        self.tokens[2] = str(value)
