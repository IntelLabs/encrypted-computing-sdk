from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `kg_seed` CInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `kg_seed` instruction requires 4 tokens:
        <line: uint>, kg_seed, <spad_src: uint>, <block_num: uint>

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "kg_seed".
        """
        return "kg_seed"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `kg_seed` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)