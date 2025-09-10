# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the bload C-instruction which loads from the SPAD to the register files."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `bload` CInstruction.

    The `bload` instruction loads metadata from the scratchpad to special registers in the register file.

    For more information, check the `bload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bload.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `bload` instruction requires 5 tokens:
        <line: uint>, bload, <meta_target_idx: uint>, <spad_src: uint>, <src_col_num: uint>

        @return The number of tokens, which is 5.
        """
        # 5 tokens:
        # <line: uint>, bload, <meta_target_idx: uint>, <spad_src: uint>, <src_col_num: uint>
        # No HBM variant:
        # <line: uint>, bload, <meta_target_idx: uint>, <spad_var_name: str>, <src_col_num: uint>
        return 5

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "bload".
        """
        return "bload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `bload` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
        self._var_name = tokens[3]
        # set spad_address to '0' if tokens[3] is a variable name
        if not tokens[3].isdigit():
            self.tokens[3] = "0"  # Should be set to SPAD address to write back.

    @property
    def var_name(self) -> str:
        """
        @brief Gets the name of the variable.

        This is a Variable name when loaded with no_hbm.

        @return The name of the variable.
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
        return int(self.tokens[3])

    @spad_address.setter
    def spad_address(self, value: int):
        self.tokens[3] = str(value)
