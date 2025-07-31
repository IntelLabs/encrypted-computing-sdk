# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the intt X-instruction which converts NTT form to positional form."""

from .xinstruction import XInstruction


class Instruction(XInstruction):
    """
    @brief Encapsulates an `intt` XInstruction.

    The Inverse Number Theoretic Transform (iNTT) converts NTT form to positional form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_intt.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `intt` instruction requires 10 tokens:
        F<bundle_idx: uint>, <info: str>, intt, <dst_top: str>, <dest_bot: str>,
        <src_top: str>, <src_bot: str>, <src_tw: str>, <stage: uint>, <res: uint>

        @return The number of tokens, which is 10.
        """
        return 10

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "intt".
        """
        return "intt"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `intt` XInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
