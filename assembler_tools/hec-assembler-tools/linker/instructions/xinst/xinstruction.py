
from linker.instructions.instruction import BaseInstruction

class XInstruction(BaseInstruction):
    """
    Represents an XInstruction, inheriting from BaseInstruction.
    """

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        Gets the index of the token containing the name of the instruction.

        Returns:
            int: The index of the name token, which is 2.
        """
        # Name at index 2.
        return 2

    # Constructor
    # -----------

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new XInstruction.

        Parameters:
            tokens (list): List of tokens for the instruction.
            comment (str): Optional comment for the instruction.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def bundle(self) -> int:
        """
        Gets the bundle index.

        Returns:
            int: The bundle index.

        Raises:
            RuntimeError: If the bundle format is invalid.
        """
        if len(self.tokens[0]) < 2 or self.tokens[0][0] != 'F':
            raise RuntimeError(f'Invalid bundle format detected: "{self.tokens[0]}".')
        return int(self.tokens[0][1:])

    @bundle.setter
    def bundle(self, value: int):
        """
        Sets the bundle index.

        Parameters:
            value (int): The new bundle index.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative bundle index, but {value} received.')
        self.tokens[0] = f'F{value}'