# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the kg_start C-instruction which initiates key generation process."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `kg_start` CInstruction.

    This instruction initiates the key generation process.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `kg_start` instruction requires 2 tokens:
        <line: uint>, kg_start

        @return The number of tokens, which is 2.
        """
        return 2

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "kg_start".
        """
        return "kg_start"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `kg_start` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
