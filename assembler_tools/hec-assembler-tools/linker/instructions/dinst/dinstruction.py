# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief This module defines the base DInstruction class for data handling instructions.

DInstruction is the parent class for all data instructions used in the
assembly process, providing common functionality and interfaces.
"""

from linker.instructions.instruction import BaseInstruction
from assembler.common.counter import Counter
from assembler.common.decorators import classproperty
from assembler.memory_model.mem_info import MemInfo


class DInstruction(BaseInstruction):
    """
    @brief Represents a DInstruction, inheriting from BaseInstruction.
    """

    _local_id_count = Counter.count(0)  # Local counter for DInstruction IDs
    _var: str = ""
    _address: int = 0

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Derived classes should implement this method and return correct
        name for the instruction.

        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        @brief Gets the index of the token containing the name of the instruction.

        @return The index of the name token, which is 0.
        """
        return 0

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Derived classes should implement this method and return correct
        required number of tokens for the instruction.

        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def num_tokens(self) -> int:
        """
        @brief Valid number of tokens for this instruction.

        @return Valid number of tokens.
        """
        return self._get_num_tokens()

    def _validate_tokens(self, tokens: list) -> None:
        """
        @brief Validates the tokens for this instruction.

        DInstruction allows at least the required number of tokens.

        @param tokens List of tokens to validate.
        @throws ValueError If tokens are invalid.
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
        @brief Constructs a new DInstruction.

        @param tokens List of tokens for the instruction.
        @param comment Optional comment for the instruction.
        """
        # Do not increment the global instruction count; skip BaseInstruction's __init__ logic for __id
        # Perform our own initialization
        super().__init__(tokens, comment=comment, count=False)

        self.comment = comment
        self._tokens = list(tokens)
        self._local_id = next(DInstruction._local_id_count)

        try:
            miv, _ = MemInfo.get_meminfo_var_from_tokens(tokens)
            miv_dict = miv.as_dict()
            self.var = miv_dict["var_name"]
            if self.name in [MemInfo.Const.Keyword.LOAD, MemInfo.Const.Keyword.STORE]:
                self.address = miv_dict["hbm_address"]
        except RuntimeError as e:
            raise ValueError(
                f"Failed to parse memory info from tokens: {tokens}. Error: {str(e)}"
            ) from e

    @property
    def id(self):
        """
        @brief Unique ID for the instruction.

        This is a combination of the client ID specified during construction and a unique nonce per instruction.

        @return (client_id: int, nonce: int) where client_id is the id specified at construction.
        """
        return self._local_id

    @property
    def var(self) -> str:
        """
        @brief Name of source/dest var.

        @return The variable name.
        """
        return self._var

    @var.setter
    def var(self, value: str):
        """
        @brief Sets the variable name.

        @param value The new variable name.
        """
        self._var = value

    @property
    def address(self) -> int:
        """
        @brief Should be set to source/dest Mem address.

        @return The memory address.
        """
        return self._address

    @address.setter
    def address(self, value: int):
        """
        @brief Sets the memory address.

        @param value The new memory address (string or integer).
        """
        self._address = value
