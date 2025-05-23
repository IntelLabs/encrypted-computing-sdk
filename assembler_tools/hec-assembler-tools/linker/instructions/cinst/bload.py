from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates the `bload` CInstruction.

    The `bload` instruction loads metadata from the scratchpad to special registers in the register file.
    
    For more information, check the `bload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bload.md
    """

    @classmethod
    def _get_num_tokens(cls)->int:
        """
        Gets the number of tokens required for the instruction.

        The `bload` instruction requires 5 tokens:
        <line: uint>, bload, <meta_target_idx: uint>, <spad_src: uint>, <src_col_num: uint>

        Returns:
            int: The number of tokens, which is 5.
        """
        # 5 tokens:
        # <line: uint>, bload, <meta_target_idx: uint>, <spad_src: uint>, <src_col_num: uint>
        # No HBM variant:
        # <line: uint>, bload, <meta_target_idx: uint>, <spad_var_name: str>, <src_col_num: uint>
        return 5

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "bload".
        """
        return "bload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `bload` CInstruction.

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
        return self.tokens[3]

    @source.setter
    def source(self, value: str):
        self.tokens[3] = value
