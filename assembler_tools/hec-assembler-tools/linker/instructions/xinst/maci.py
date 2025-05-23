from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates a `maci` XInstruction.

    Element-wise polynomial scaling by an immediate value and accumulation.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_maci.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `maci` instruction requires 8 tokens:
        F<bundle_idx: uint>, <info: str>, maci, <dst: str>, <src0: str>, <src1: str>, <imm: str>, <res: uint>

        Returns:
            int: The number of tokens, which is 8.
        """
        return 8

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "maci".
        """
        return "maci"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `maci` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)