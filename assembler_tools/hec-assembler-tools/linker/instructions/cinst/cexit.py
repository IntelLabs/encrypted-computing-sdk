from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `cexit` CInstruction.
    
    This instruction terminates execution of a HERACLES program.

    For more information, check the `cexit` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cexit.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `cexit` instruction requires 2 tokens:
        <line: uint>, cexit

        Returns:
            int: The number of tokens, which is 2.
        """
        return 2

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "cexit".
        """
        return "cexit"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `cexit` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)