from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates an `ifetch` CInstruction.

    This instruction fetches a bundle of instructions from the XINST queue and sends it to the CE for execution.

    For more information, check the `ifetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_ifetch.md

    Properties:
        bundle: Gets or sets the target bundle index.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `ifetch` instruction requires 3 tokens:
        <line: uint>, ifetch, <bundle_idx: uint>

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "ifetch".
        """
        return "ifetch"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `ifetch` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def bundle(self) -> int:
        """
        Gets the target bundle index.

        Returns:
            int: The target bundle index.
        """
        return int(self.tokens[2])

    @bundle.setter
    def bundle(self, value: int):
        """
        Sets the target bundle index.

        Args:
            value (int): The target bundle index to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative bundle index, but {value} received.')
        self.tokens[2] = str(value)