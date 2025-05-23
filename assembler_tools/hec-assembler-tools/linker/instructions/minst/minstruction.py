
from linker.instructions.instruction import BaseInstruction

class MInstruction(BaseInstruction):
    """
    Represents an MInstruction, inheriting from BaseInstruction.
    """

    @classmethod
    def _get_name_token_index(cls) -> int:
        """
        Gets the index of the token containing the name of the instruction.

        Returns:
            int: The index of the name token, which is 1.
        """
        return 1

    # Constructor
    # -----------

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new MInstruction.

        Parameters:
            tokens (list): List of tokens for the instruction.
            comment (str): Optional comment for the instruction.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    def to_line(self) -> str:
        """
        Retrieves the string form of the instruction to write to the instruction file.

        Returns:
            str: The string representation of the instruction, excluding the first token.
        """
        return ", ".join(self.tokens[1:])