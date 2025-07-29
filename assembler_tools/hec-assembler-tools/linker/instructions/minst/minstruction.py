# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the base class for all M-instructions."""

from linker.instructions.instruction import BaseInstruction


class MInstruction(BaseInstruction):
    """
    @brief Represents an MInstruction, inheriting from BaseInstruction.
    """

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Returns the name of the instruction.

        @return The instruction name.
        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        @brief Gets the index of the token containing the name of the instruction.

        @return The index of the name token, which is 1.
        """
        return 1

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Returns the required number of tokens for the instruction.

        @return The number of required tokens.
        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    # Constructor
    # -----------

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Constructs a new MInstruction.

        @param tokens List of tokens for the instruction.
        @param comment Optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    def to_line(self) -> str:
        """
        Retrieves the string form of the instruction to write to the instruction file.

        Returns:
            str: The string representation of the instruction, excluding the first token.
        """
        return ", ".join(self.tokens[1:])
