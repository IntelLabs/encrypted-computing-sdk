# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Base class for all instructions in the linker.
"""

from assembler.common.decorators import classproperty
from assembler.common.counter import Counter
from assembler.common.config import GlobalConfig


class BaseInstruction:
    """
    @brief Base class for all instructions.

    This class provides common functionality for all instructions in the linker.

    @var comment Comment for the instruction.

    @property name Returns the name of the represented operation.
    @property tokens List of tokens for the instruction.
    @property id Unique instruction ID. This is a unique nonce representing the instruction.

    @fn to_line Retrieves the string form of the instruction to write to the instruction file.
    """

    __id_count = Counter.count(
        0
    )  # Internal unique sequence counter to generate unique IDs

    # Class methods and properties
    # ----------------------------

    @classproperty
    def name(self) -> str:
        """
        @brief Name for the instruction.

        @return The name of the instruction.
        """
        return self._get_name()

    @classmethod
    def _get_name(cls) -> str:
        """
        @brief Derived classes should implement this method and return correct
        name for the instruction.

        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def name_token_index(self) -> int:
        """
        @brief Index for the token containing the name of the instruction
        in the list of tokens.

        @return The index of the name token.
        """
        return self._get_name_token_index()

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        @brief Derived classes should implement this method and return correct
        index for the token containing the name of the instruction
        in the list of tokens.

        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def num_tokens(self) -> int:
        """
        @brief Number of tokens required for this instruction.

        @return The number of tokens required.
        """
        return self._get_num_tokens()

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        @brief Derived classes should implement this method and return correct
        required number of tokens for the instruction.

        @throws NotImplementedError Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classmethod
    def dump_instructions_to_file(cls, instructions: list, filename: str):
        """
        @brief Writes a list of instruction objects to a file, one per line.

        Each instruction is converted to its string representation using the `to_line()` method.

        @param instructions List of instruction objects (must have a to_line() method).
        @param filename Path to the output file.
        """
        with open(filename, "w", encoding="utf-8") as f:
            for instr in instructions:
                f.write(instr.to_line() + "\n")

    # Constructor
    # -----------

    def __init__(self, tokens: list, comment: str = ""):
        """
        @brief Creates a new BaseInstruction object.

        @param tokens List of tokens for the instruction.
        @param comment Optional comment for the instruction.
        @throws ValueError If the number of tokens is invalid or the instruction name is incorrect.
        """
        assert self.name_token_index < self.num_tokens

        self._validate_tokens(tokens)

        self._id = next(BaseInstruction.__id_count)

        self._tokens = list(tokens)
        self.comment = comment

    def _validate_tokens(self, tokens: list) -> None:
        """
        @brief Validates the tokens for this instruction.

        Default implementation checks for exact token count match.
        Child classes can override this method to implement different validation logic.

        @param tokens List of tokens to validate.
        @throws ValueError If tokens are invalid.
        """
        if len(tokens) != self.num_tokens:  # pylint: disable=W0143
            raise ValueError(
                f"`tokens`: invalid amount of tokens. "
                f"Instruction {self.name} requires exactly {self.num_tokens}, but {len(tokens)} received"
            )

        if tokens[self.name_token_index] != self.name:  # pylint: disable=W0143
            raise ValueError(
                f"`tokens`: invalid name. Expected {self.name}, but {tokens[self.name_token_index]} received"
            )

    def __repr__(self):
        retval = f"<{type(self).__name__}({self.name}, id={self.id}) object at {hex(id(self))}>(tokens={self.tokens})"
        return retval

    def __eq__(self, other):
        # Equality operator== overload
        return self is other

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f"{self.name}({self.id})"

    # Methods and properties
    # ----------------------------

    @property
    def id(self) -> tuple:
        """
        @brief Unique ID for the instruction.

        This is a combination of the client ID specified during construction and a unique nonce per instruction.

        @return (client_id: int, nonce: int) where client_id is the id specified at construction.
        """
        return self._id

    @property
    def tokens(self) -> list:
        """
        @brief Gets the list of tokens for the instruction.

        @return The list of tokens.
        """
        return self._tokens

    def to_line(self) -> str:
        """
        @brief Retrieves the string form of the instruction to write to the instruction file.

        @return The string representation of the instruction.
        """
        comment_str = ""
        if not GlobalConfig.suppress_comments:
            comment_str = f" # {self.comment}" if self.comment else ""

        tokens_str = ", ".join(self.tokens)
        return f"{tokens_str}{comment_str}"
