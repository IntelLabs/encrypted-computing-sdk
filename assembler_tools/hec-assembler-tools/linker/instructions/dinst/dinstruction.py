# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
This module defines the base DInstruction class for data handling instructions.

DInstruction is the parent class for all data instructions used in the
assembly process, providing common functionality and interfaces.
"""

from linker.instructions.instruction import BaseInstruction
from assembler.common.counter import Counter
from assembler.common.decorators import classproperty


class DInstruction(BaseInstruction):
    """
    Represents a DInstruction, inheriting from BaseInstruction.
    """

    _local_id_count = Counter.count(0)  # Local counter for DInstruction IDs
    _var: str = ""
    _address: int = 0

    @classmethod
    def _get_name(cls) -> str:
        """
        Derived classes should implement this method and return correct
        name for the instruction.

        Raises:
            NotImplementedError: Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        Gets the index of the token containing the name of the instruction.

        Returns:
            int: The index of the name token, which is 0.
        """
        return 0

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Derived classes should implement this method and return correct
        required number of tokens for the instruction.

        Raises:
            NotImplementedError: Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def num_tokens(self) -> int:
        """
        Valid number of tokens for this instruction.

        Returns:
            tuple: Valid number of tokens.
        """
        return self._get_num_tokens()

    def _validate_tokens(self, tokens: list) -> None:
        """
        Validates the tokens for this instruction.

        DInstruction allows at least the required number of tokens.

        Parameters:
            tokens (list): List of tokens to validate.

        Raises:
            ValueError: If tokens are invalid.
        """
        assert self.name_token_index < self.num_tokens
        if len(tokens) < self.num_tokens:
            raise ValueError(
                f"`tokens`: invalid amount of tokens. "
                f"Instruction {self.name} requires at least {self.num_tokens}, but {len(tokens)} received"
            )
        if tokens[self.name_token_index] != self.name:
            raise ValueError(
                f"`tokens`: invalid name. Expected {self.name}, but {tokens[self.name_token_index]} received"
            )

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new DInstruction.

        Parameters:
            tokens (list): List of tokens for the instruction.
            comment (str): Optional comment for the instruction.
        """
        # Do not increment the global instruction count; skip BaseInstruction's __init__ logic for __id
        # Call BaseInstruction constructor but perform our own initialization
        super().__init__(tokens, comment=comment)

        self.comment = comment
        self._tokens = list(tokens)
        self._local_id = next(DInstruction._local_id_count)

    @property
    def id(self):
        """
        Unique ID for the instruction.

        This is a combination of the client ID specified during construction and a unique nonce per instruction.

        Returns:
            tuple: (client_id: int, nonce: int) where client_id is the id specified at construction.
        """
        return self._local_id

    @property
    def var(self) -> str:
        """
        Name of source/dest var.
        """
        return self._var

    @var.setter
    def var(self, value: str):
        self._var = value

    @property
    def address(self) -> int:
        """
        Should be set to source/dest Mem address.
        """
        return self._address

    @address.setter
    def address(self, value: str):
        self._address = int(value) if isinstance(value, str) else value

    def to_line(self) -> str:
        """
        Retrieves the string form of the instruction to write to the instruction file.

        Returns:
            str: The string representation of the instruction.
        """
        return ", ".join(self.tokens)
