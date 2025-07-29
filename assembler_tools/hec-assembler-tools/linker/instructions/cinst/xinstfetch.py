# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the xinstfetch C-instruction which fetches X-instructions from memory."""

from .cinstruction import CInstruction


class Instruction(CInstruction):
    """
    @brief Encapsulates an `xinstfetch` CInstruction.

    This instruction fetches instructions from the HBM and sends them to the XINST queue.

    For more information, check the `xinstfetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_xinstfetch.md

    Properties:
        dst_x_queue: Gets or sets the destination in the XINST queue.
        src_hbm: Gets or sets the source in the HBM.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Gets the number of tokens required for the instruction.

        The `xinstfetch` instruction requires 4 tokens:
        <line: uint>, xinstfetch, <xq_dst:uint>, <hbm_src: uint>

        @return The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Gets the name of the instruction.

        @return The name of the instruction, which is "xinstfetch".
        """
        return "xinstfetch"

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new `xinstfetch` CInstruction.

        @param tokens A list of tokens representing the instruction.
        @param comment An optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)
        raise NotImplementedError(
            "`xinstfetch` CInstruction is not currently supported in linker."
        )

    @property
    def dst_x_queue(self) -> int:
        """
        @brief Gets the destination in the XINST queue.

        @return The destination in the XINST queue.
        """
        return int(self.tokens[2])

    @dst_x_queue.setter
    def dst_x_queue(self, value: int):
        """
        @brief Sets the destination in the XINST queue.

        @param value The destination value to set.
        @throws ValueError If the value is negative.
        """
        if value < 0:
            raise ValueError(
                f"`value`: expected non-negative value, but {value} received."
            )
        self.tokens[2] = str(value)

    @property
    def src_hbm(self) -> int:
        """
        @brief Gets the source in the HBM.

        @return The source in the HBM.
        """
        return int(self.tokens[3])

    @src_hbm.setter
    def src_hbm(self, value: int):
        """
        @brief Sets the source in the HBM.

        @param value The source value to set.
        @throws ValueError If the value is negative.
        """
        if value < 0:
            raise ValueError(
                f"`value`: expected non-negative value, but {value} received."
            )
        self.tokens[3] = str(value)
