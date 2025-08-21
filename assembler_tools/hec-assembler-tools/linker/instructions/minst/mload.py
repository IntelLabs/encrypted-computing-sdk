# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the mload M-instruction which loads data from memory to scratchpad."""

from .minstruction import MInstruction


class Instruction(MInstruction):
    """
    @brief Encapsulates an `mload` MInstruction.

    This instruction loads a single polynomial residue from local memory to scratchpad.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mload.md

    Properties:
        source: Gets or sets the name of the source.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `mload` instruction requires 4 tokens:
        <line: uint>, mload, <dst: uint>, <src_var: str>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "mload".
        """
        return "mload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `mload` MInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
        self._var_name = tokens[3]
        self.tokens[3] = "0"  # Should be set to HBM address to write back.

    @property
    def var_name(self) -> str:
        """
        @brief Gets the name of the source variable.

        This is a Variable name.

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
    def hbm_address(self) -> int:
        """
        @brief Source HBM address.

        Should be set to HBM address to write back.

        @return The HBM source.
        """
        return int(self.tokens[3])

    @hbm_address.setter
    def hbm_address(self, value: int):
        """
        @brief Sets the address of the source.

        @param value The address of the source to set.
        """
        self.tokens[3] = str(value)

    @property
    def spad_address(self) -> int:
        """
        @brief Gets the destination index.

        This is the index in the scratchpad where the data will be loaded.

        @return The destination index.
        """
        return int(self.tokens[2])

    @spad_address.setter
    def spad_address(self, value: int):
        """
        @brief Sets the destination index.

        @param value The destination index to set.
        """
        self.tokens[2] = str(value)
