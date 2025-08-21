# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the cload C-instruction which loads data from SPAD to registers."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `cload` CInstruction.

    This instruction loads a single polynomial residue from scratchpad into a register.

    For more information, check the `cload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cload.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `cload` instruction requires 4 tokens:
        <line: uint>, cload, <dst: str>, <src: uint>

        @return The number of tokens, which is 4.
        """
        # 4 tokens:
        # <line: uint>, cload, <dst: str>, <src: uint>
        # No HBM variant
        # <line: uint>, cload, <dst: str>, <src_var_name: str>
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "cload".
        """
        return "cload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `cload` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
        self._var_name = tokens[3]
        if not tokens[3].isdigit():
            self.tokens[3] = "-1"  # Should be set to SPAD address to write back.

    @property
    def var_name(self) -> str:
        """
        @brief Gets the name of the original source variable.

        This is a Variable name when there is no HBM.
        """
        return self._var_name

    @var_name.setter
    def var_name(self, value: str):
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

    @property
    def register(self) -> str:
        """
        @brief Gets the name of the destination register.
        """
        return self.tokens[2]

    @register.setter
    def register(self, value: str):
        """
        @brief Sets the name of the destination register.

        @param value The name of the register to set.
        """
        self.tokens[2] = value
