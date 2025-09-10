# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the twintt X-instruction which generates twiddle factors for the next stage of iNTT."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates a `twintt` XInstruction.

    This instruction performs on-die generation of twiddle factors for the next stage of iNTT.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_twintt.md.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `twintt` instruction requires 10 tokens:
        F<bundle_idx: uint>, <info: str>, twintt, <dst_tw: str>, <src_tw: str>,
        <tw_meta: uint>, <stage: uint>, <block: uint>, <ring_dim: uint>, <res: uint>

        @return The number of tokens, which is 10.
        """
        return 10

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "twintt".
        """
        return "twintt"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `twintt` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def dest(self) -> str:
        """
        @brief Retrieves the destination register of the instruction.
        @return The destination register as a string.
        """
        return self.tokens[3]

    @dest.setter
    def dest(self, value: str):
        """
        @brief Sets the destination register of the instruction.
        @param value The new destination register as a string.
        """
        self.tokens[3] = value
