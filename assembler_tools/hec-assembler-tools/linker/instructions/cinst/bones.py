from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `bones` CInstruction.
    
    The `bones` instruction loads metadata of identity (one) from the scratchpad to the register file.
    
    For more information, check the `bones` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bones.md
    """

    @classmethod
    def _get_num_tokens(cls)->int:
        """
        Gets the number of tokens required for the instruction.

        The `bones` instruction requires 4 tokens:
        <line: uint>, bones, <spad_src: uint>, <col_num: uint>

        Returns:
            int: The number of tokens, which is 4.
        """
        # 4 tokens:
        # <line: uint>, bones, <spad_src: uint>, <col_num: uint>
        # No HBM variant:
        # <line: uint>, bones, <spad_var_name: str>, <col_num: uint>
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "bones".
        """
        return "bones"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `bones` CInstruction.

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
        Name of the source.
        This is a Variable name when loaded. Should be set to HBM address to write back.
        """
        return self.tokens[2]

    @source.setter
    def source(self, value: str):
        self.tokens[2] = value
