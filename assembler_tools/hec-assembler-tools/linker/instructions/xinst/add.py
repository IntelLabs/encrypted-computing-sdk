from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates an `add` XInstruction.

    This instruction adds two polynomials stored in the register file and
    stores the result in a register.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_add.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `add` instruction requires 7 tokens:
        F<bundle_idx: uint>, <info: str>, add, <dst: str>, <src0: str>, <src1: str>, <res: uint>

        Returns:
            int: The number of tokens, which is 7.
        """
        return 7

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "add".
        """
        return "add"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `add` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)