from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `kg_start` CInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `kg_start` instruction requires 2 tokens:
        <line: uint>, kg_start

        Returns:
            int: The number of tokens, which is 2.
        """
        return 2

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "kg_start".
        """
        return "kg_start"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `kg_start` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)