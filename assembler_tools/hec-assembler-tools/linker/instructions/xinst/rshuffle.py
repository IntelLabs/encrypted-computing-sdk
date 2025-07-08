# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the rshuffle X-instruction which performs data shuffling operations."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `rshuffle` XInstruction.

    This instruction performs data shuffling operations between registers.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `rshuffle` instruction requires 9 tokens:
        F<bundle_idx: uint>, <info: str>, rshuffle, <dst0: str>, <dst1: str>, <src0: str>, <src1: str>, <wait_cyc: uint>, <data_type: str>

        @return The number of tokens, which is 9.
        """
        return 9

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "rshuffle".
        """
        return "rshuffle"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `rshuffle` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
