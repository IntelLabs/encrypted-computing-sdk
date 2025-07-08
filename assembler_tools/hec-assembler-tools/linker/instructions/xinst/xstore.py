# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the xstore X-instruction which transfers data from a register to the intermediate data buffer."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `xstore` XInstruction.

    This instruction transfers data from a register into the intermediate data buffer for subsequent transfer into SPAD.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_xstore.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `xstore` instruction requires 4 tokens:
        F<bundle_idx: uint>, <info: str>, xstore, <src: str>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "xstore".
        """
        return "xstore"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `xstore` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
