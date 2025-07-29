# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module implements the base class for all X-instructions."""

from linker.instructions.instruction import BaseInstruction


class XInstruction(BaseInstruction):
    """
    @brief Represents an XInstruction, inheriting from BaseInstruction.
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

        @return The index of the name token, which is 2.
        """
        # Name at index 2.
        return 2

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
        @brief Constructs a new XInstruction.

        @param tokens List of tokens for the instruction.
        @param comment Optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def bundle(self) -> int:
        """
        @brief Gets the bundle index.

        @return The bundle index.
        @throws RuntimeError If the bundle format is invalid.
        """
        if len(self.tokens[0]) < 2 or self.tokens[0][0] != "F":
            raise RuntimeError(f'Invalid bundle format detected: "{self.tokens[0]}".')
        return int(self.tokens[0][1:])

    @bundle.setter
    def bundle(self, value: int):
        """
        @brief Sets the bundle index.

        @param value The new bundle index.
        @throws ValueError If the value is negative.
        """
        if value < 0:
            raise ValueError(
                f"`value`: expected non-negative bundle index, but {value} received."
            )
        self.tokens[0] = f"F{value}"
