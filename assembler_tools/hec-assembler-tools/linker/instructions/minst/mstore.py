from .minstruction import MInstruction

class Instruction(MInstruction):
    """
    Encapsulates an `mstore` MInstruction.

    This instruction stores a single polynomial residue from scratchpad to local memory.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mstore.md

    Properties:
        dest: Gets or sets the name of the destination.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `mstore` instruction requires 4 tokens:
        <line: uint>, mstore, <dst_var: str>, <src: uint>

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "mstore".
        """
        return "mstore"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `mstore` MInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)

    @property
    def dest(self) -> str:
        """
        Gets the name of the destination.

        This is a Variable name when loaded. Should be set to HBM address to write back.

        Returns:
            str: The name of the destination.
        """
        return self.tokens[2]

    @dest.setter
    def dest(self, value: str):
        """
        Sets the name of the destination.

        Args:
            value (str): The name of the destination to set.
        """
        self.tokens[2] = value