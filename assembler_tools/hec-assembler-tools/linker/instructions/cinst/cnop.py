from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `cnop` CInstruction.

    This instruction adds a desired amount of idle cycles in the Cfetch flow.

    For more information, check the `cnop` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nop.md

    Properties:
        cycles: Gets or sets the number of idle cycles.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `cnop` instruction requires 3 tokens:
        <line: uint>, cnop, <cycles: uint>

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "cnop".
        """
        return "cnop"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `cnop` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def cycles(self) -> int:
        """
        Gets the number of idle cycles.

        Returns:
            int: The number of idle cycles.
        """
        return int(self.tokens[2])

    @cycles.setter
    def cycles(self, value: int):
        """
        Sets the number of idle cycles.

        Args:
            value (int): The number of idle cycles to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value` must be non-negative, but {value} received.')
        self.tokens[2] = str(value)