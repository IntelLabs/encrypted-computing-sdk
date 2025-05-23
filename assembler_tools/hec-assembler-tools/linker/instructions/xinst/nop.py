from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates a `nop` XInstruction.

    This instruction adds a desired amount of idle cycles to the compute flow.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_nop.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `nop` instruction requires 4 tokens:
        F<bundle_idx: uint>, <info: str>, nop, <idle_cycles: uint32>

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "nop".
        """
        return "nop"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `nop` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)