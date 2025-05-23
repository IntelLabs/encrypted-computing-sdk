from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `cstore` CInstruction.

    This instruction fetches a single polynomial residue from the intermediate data buffer and stores it back to SPAD.

    For more information, check the `cstore` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cstore.md
    """

    @classmethod
    def _get_num_tokens(cls)->int:
        """
        Gets the number of tokens required for the instruction.

        The `cstore` instruction requires 3 tokens:
        <line: uint>, cstore, <dst: uint>

        Returns:
            int: The number of tokens, which is 3.
        """
        # 3 tokens:
        # <line: uint>, cstore, <dst: uint>
        # No HBM variant
        # <line: uint>, cstore, <dst_var_name: str>
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "cstore".
        """
        return "cstore"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `cstore` CInstruction.

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
        Name of the destination.
        This is a Variable name when loaded. Should be set to HBM address to write back.
        """
        return self.tokens[2]

    @dest.setter
    def dest(self, value: str):
        self.tokens[2] = value
