from .minstruction import MInstruction

class Instruction(MInstruction):
    """
    Encapsulates an `mload` MInstruction.

    This instruction loads a single polynomial residue from local memory to scratchpad.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mload.md

    Properties:
        source: Gets or sets the name of the source.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `mload` instruction requires 4 tokens:
        <line: uint>, mload, <dst: uint>, <src_var: str>

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "mload".
        """
        return "mload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `mload` MInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def source(self) -> str:
        """
        Gets the name of the source.

        This is a Variable name when loaded. Should be set to HBM address to write back.

        Returns:
            str: The name of the source.
        """
        return self.tokens[3]

    @source.setter
    def source(self, value: str):
        """
        Sets the name of the source.

        Args:
            value (str): The name of the source to set.
        """
        self.tokens[3] = value