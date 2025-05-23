from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `csyncm` CInstruction.
    
    Wait instruction similar to a barrier that stalls the execution of the CINST
    queue until the specified instruction from the MINST queue has completed.

    For more information, check the `csyncm` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_csyncm.md

    Properties:
        target: Gets or sets the target MInst.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `csyncm` instruction requires 3 tokens:
        <line: uint>, csyncm, <inst_num: uint>

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "csyncm".
        """
        return "csyncm"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `csyncm` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def target(self) -> int:
        """
        Gets the target MInst.

        Returns:
            int: The target MInst.
        """
        return int(self.tokens[2])

    @target.setter
    def target(self, value: int):
        """
        Sets the target MInst.

        Args:
            value (int): The target MInst to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative target, but {value} received.')
        self.tokens[2] = str(value)