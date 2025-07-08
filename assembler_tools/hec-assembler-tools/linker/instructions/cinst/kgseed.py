# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the kgseed C-instruction which loads key generation seed data."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `kg_seed` CInstruction.

    This instruction loads key generation seed data.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `kg_seed` instruction requires 4 tokens:
        <line: uint>, kg_seed, <spad_src: uint>, <block_num: uint>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "kg_seed".
        """
        return "kg_seed"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `kg_seed` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
