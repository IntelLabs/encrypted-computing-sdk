from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates an `bexit` XInstruction.

    This instruction terminates execution of an instruction bundle.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_exit.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `bexit` instruction requires 3 tokens:
        F<bundle_idx: uint>, <info: str>, bexit

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "bexit".
        """
        return "bexit"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `bexit` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)