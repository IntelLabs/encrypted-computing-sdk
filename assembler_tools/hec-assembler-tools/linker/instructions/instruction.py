from assembler.common.decorators import *
from assembler.common.counter import Counter

class BaseInstruction:
    """
    Base class for all instructions.

    This class provides common functionality for all instructions in the linker.

    Class Properties:
        name (str): Returns the name of the represented operation.

    Attributes:
        comment (str): Comment for the instruction.

    Properties:
        tokens (list[str]): List of tokens for the instruction.
        id (int): Unique instruction ID. This is a unique nonce representing the instruction.

    Methods:
        to_line(self) -> str:
            Retrieves the string form of the instruction to write to the instruction file.
    """

    __id_count = Counter.count(0)  # Internal unique sequence counter to generate unique IDs

    # Class methods and properties
    # ----------------------------

    @classproperty
    def name(cls) -> str:
        """
        Name for the instruction.

        Returns:
            str: The name of the instruction.
        """
        return cls._get_name()

    @classmethod
    def _get_name(cls) -> str:
        """
        Derived classes should implement this method and return correct
        name for the instruction.

        Raises:
            NotImplementedError: Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def NAME_TOKEN_INDEX(cls) -> int:
        """
        Index for the token containing the name of the instruction
        in the list of tokens.

        Returns:
            int: The index of the name token.
        """
        return cls._get_name_token_index()

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        Derived classes should implement this method and return correct
        index for the token containing the name of the instruction
        in the list of tokens.

        Raises:
            NotImplementedError: Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    @classproperty
    def NUM_TOKENS(cls) -> int:
        """
        Number of tokens required for this instruction.

        Returns:
            int: The number of tokens required.
        """
        return cls._get_num_tokens()

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Derived classes should implement this method and return correct
        required number of tokens for the instruction.

        Raises:
            NotImplementedError: Abstract method. This base method should not be called.
        """
        raise NotImplementedError()

    # Constructor
    # -----------

    def __init__(self, tokens: list, comment: str = ""):
        """
        Creates a new BaseInstruction object.

        Parameters:
            tokens (list): List of tokens for the instruction.
            comment (str): Optional comment for the instruction.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        assert self.NAME_TOKEN_INDEX < self.NUM_TOKENS

        if len(tokens) != self.NUM_TOKENS:
            raise ValueError(('`tokens`: invalid amount of tokens. '
                              'Instruction {} requires {}, but {} received').format(self.name,
                                                                                    self.NUM_TOKENS,
                                                                                    len(tokens)))
        if tokens[self.NAME_TOKEN_INDEX] != self.name:
            raise ValueError('`tokens`: invalid name. Expected {}, but {} received'.format(self.name,
                                                                                           tokens[self.NAME_TOKEN_INDEX]))

        self.__id = next(BaseInstruction.__id_count)

        self.__tokens = list(tokens)
        self.comment = comment

    def __repr__(self):
        retval = ('<{}({}, id={}) object at {}>(tokens={})').format(type(self).__name__,
                                                                    self.name,
                                                                    self.id,
                                                                    hex(id(self)),
                                                                    self.token)
        return retval

    def __eq__(self, other):
        # Equality operator== overload
        return self is other

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return f'{self.name}({self.id})'

    # Methods and properties
    # ----------------------------

    @property
    def id(self) -> tuple:
        """
        Unique ID for the instruction.

        This is a combination of the client ID specified during construction and a unique nonce per instruction.

        Returns:
            tuple: (client_id: int, nonce: int) where client_id is the id specified at construction.
        """
        return self.__id

    @property
    def tokens(self) -> list:
        """
        Gets the list of tokens for the instruction.

        Returns:
            list: The list of tokens.
        """
        return self.__tokens

    def to_line(self) -> str:
        """
        Retrieves the string form of the instruction to write to the instruction file.

        Returns:
            str: The string representation of the instruction.
        """
        return ", ".join(self.tokens)