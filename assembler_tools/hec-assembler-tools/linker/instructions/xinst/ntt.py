# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the ntt X-instruction which converts positional form to NTT form."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `ntt` XInstruction (Number Theoretic Transform).

    Converts positional form to NTT form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_ntt.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `ntt` instruction requires 10 tokens:
        F<bundle_idx: uint>, <info: str>, ntt, <dst_top: str>, <dest_bot: str>,
         <src_top: str>, <src_bot: str>, <src_tw: str>, <stage: uint>, <res: uint>

        @return The number of tokens, which is 10.
        """
        return 10

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "ntt".
        """
        return "ntt"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `ntt` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def dest0(self) -> str:
        """
        @brief Retrieves the destination register of the instruction.
        @return The destination register as a string.
        """
        return self.tokens[3]

    @dest0.setter
    def dest0(self, value: str):
        """
        @brief Sets the destination register of the instruction.
        @param value The new destination register as a string.
        """
        self.tokens[3] = value

    @property
    def dest1(self) -> str:
        """
        @brief Retrieves the destination register of the instruction.
        @return The destination register as a string.
        """
        return self.tokens[4]

    @dest1.setter
    def dest1(self, value: str):
        """
        @brief Sets the destination register of the instruction.
        @param value The new destination register as a string.
        """
        self.tokens[4] = value
