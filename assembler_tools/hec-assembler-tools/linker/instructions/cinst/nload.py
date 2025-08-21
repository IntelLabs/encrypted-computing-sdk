# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the nload C-instruction which loads NTT tables from SPAD."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates an `nload` CInstruction.

    This instruction loads metadata (for NTT/iNTT routing mapping) from
    scratchpad into a special routing table register.

    For more information, check the `nload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nload.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `nload` instruction requires 4 tokens:
        <line: uint>, nload, <table_idx_dst: uint>, <spad_src: uint>

        @return The number of tokens, which is 4.
        """
        # 4 tokens:
        # <line: uint>, nload, <table_idx_dst: uint>, <spad_src: uint>
        # No HBM variant:
        # <line: uint>, nload, <table_idx_dst: uint>, <spad_var_name: uint>
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "nload".
        """
        return "nload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `nload` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
        self._var_name = tokens[3]
        if not tokens[3].isdigit():
            self.tokens[3] = "0"  # Should be set to SPAD address to write back.

    @property
    def var_name(self) -> str:
        """
        @brief Gets the name of the variable.

        This is a Variable name when there is no HBM.
        """
        return self._var_name

    @var_name.setter
    def var_name(self, value: str):
        """
        @brief Sets the name of the variable.

        This is a Variable name.
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
