from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates a `muli` XInstruction.

    This instruction performs element-wise polynomial scaling by an immediate value.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_muli.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `muli` instruction requires 7 tokens:
        F<bundle_idx: uint>, <info: str>, muli, <dst: str>, <src: str>, <imm: str>, <res: uint>

        Returns:
            int: The number of tokens, which is 7.
        """
        return 7

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "muli".
        """
        return "muli"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `muli` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)