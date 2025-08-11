# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the cstore C-instruction which stores data to SPAD."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates a `cstore` CInstruction.

    This instruction fetches a single polynomial residue from the intermediate data buffer and stores it back to SPAD.

    For more information, check the `cstore` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cstore.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `cstore` instruction requires 3 tokens:
        <line: uint>, cstore, <dst: uint>

        @return The number of tokens, which is 3.
        """
        # 3 tokens:
        # <line: uint>, cstore, <dst: uint>
        # No HBM variant
        # <line: uint>, cstore, <dst_var_name: str>
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "cstore".
        """
        return "cstore"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `cstore` CInstruction.

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
        @brief Name of the destination.
        Should be set to HBM address to write back.

        @return The destination variable address.
        """
        return int(self.tokens[2])

    @spad_address.setter
    def spad_address(self, value: int):
        """
        @brief Sets the destination of the instruction.

        @param value The new destination value to set.
        """
        self.tokens[2] = str(value)
