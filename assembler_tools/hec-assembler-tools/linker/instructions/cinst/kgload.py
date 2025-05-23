from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `kg_load` CInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `kg_load` instruction requires 3 tokens:
        <line: uint>, kg_load, <dst: str>

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "kg_load".
        """
        return "kg_load"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `kg_load` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)