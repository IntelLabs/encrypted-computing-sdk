# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the maci X-instruction which performs element-wise polynomial scaling by an immediate value and accumulation."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates a `maci` XInstruction.

    Element-wise polynomial scaling by an immediate value and accumulation.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_maci.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `maci` instruction requires 8 tokens:
        F<bundle_idx: uint>, <info: str>, maci, <dst: str>, <src0: str>, <src1: str>, <imm: str>, <res: uint>

        @return The number of tokens, which is 8.
        """
        return 8

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "maci".
        """
        return "maci"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `maci` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
