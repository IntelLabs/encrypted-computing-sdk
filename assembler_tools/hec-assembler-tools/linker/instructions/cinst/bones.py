# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the bones C-instruction which loads a ones buffer from SPAD to registers."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `bones` CInstruction.

    The `bones` instruction loads metadata of identity (one) from the scratchpad to the register file.

    For more information, check the `bones` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bones.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `bones` instruction requires 4 tokens:
        <line: uint>, bones, <spad_src: uint>, <col_num: uint>

        @return The number of tokens, which is 4.
        """
        # 4 tokens:
        # <line: uint>, bones, <spad_src: uint>, <col_num: uint>
        # No HBM variant:
        # <line: uint>, bones, <spad_var_name: str>, <col_num: uint>
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "bones".
        """
        return "bones"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `bones` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def source(self) -> str:
        """
        @brief Name of the source.
        This is a Variable name when loaded. Should be set to HBM address to write back.
        """
        return self.tokens[2]

    @source.setter
    def source(self, value: str):
        self.tokens[2] = value
