from .minstruction import MInstruction

class Instruction(MInstruction):
    """
    Encapsulates an `msyncc` MInstruction.

    Wait instruction similar to a barrier that stalls the execution of the MINST
    queue until the specified instruction from the CINST queue has completed.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_msyncc.md

    Properties:
        target: Gets or sets the target CInst.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `msyncc` instruction requires 3 tokens:
        <line: uint>, msyncc, <target: uint>

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "msyncc".
        """
        return "msyncc"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `msyncc` MInstruction.

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
        Gets the target CInst.

        Returns:
            int: The target CInst.
        """
        return int(self.tokens[2])

    @target.setter
    def target(self, value: int):
        """
        Sets the target CInst.

        Args:
            value (int): The target CInst to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative target, but {value} received.')
        self.tokens[2] = str(value)