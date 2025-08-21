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
        self._var_name = tokens[2]
        if not tokens[2].isdigit():
            self.tokens[2] = "0"  # Should be set to SPAD address to write back.

    @property
    def var_name(self) -> str:
        """
        @brief Gets the name of the variable.

        This is a Variable name when loaded and there is no HBM.
        """
        return self._var_name

    @var_name.setter
    def var_name(self, value: str):
        """
        @brief Sets the name of the variable.

        @param value The name of the variable to set.
        """
        self._var_name = value

    @property
    def spad_address(self) -> int:
        """
        @brief Source SPAD address.
        """
        return int(self.tokens[2])

    @spad_address.setter
    def spad_address(self, value: int):
        self.tokens[2] = str(value)
