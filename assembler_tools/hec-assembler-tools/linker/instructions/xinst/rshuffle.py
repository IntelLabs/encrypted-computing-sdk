from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates an `rshuffle` XInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `rshuffle` instruction requires 9 tokens:
        F<bundle_idx: uint>, <info: str>, rshuffle, <dst0: str>, <dst1: str>, <src0: str>, <src1: str>, <wait_cyc: uint>, <data_type: str>

        Returns:
            int: The number of tokens, which is 9.
        """
        return 9

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "rshuffle".
        """
        return "rshuffle"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `rshuffle` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)