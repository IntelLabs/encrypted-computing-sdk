from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates a `move` XInstruction.

    This instruction copies data from one register to a different one.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_move.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `move` instruction requires 5 tokens:
        F<bundle_idx: uint>, <info: str>, move, <dst: str>, <src: str>

        Returns:
            int: The number of tokens, which is 5.
        """
        return 5

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "move".
        """
        return "move"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `move` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)