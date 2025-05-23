from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `nload` CInstruction.

    This instruction loads metadata (for NTT/iNTT routing mapping) from
    scratchpad into a special routing table register.

    For more information, check the `nload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nload.md
    """

    @classmethod
    def _get_num_tokens(cls)->int:
        """
        Gets the number of tokens required for the instruction.

        The `nload` instruction requires 4 tokens:
        <line: uint>, nload, <table_idx_dst: uint>, <spad_src: uint>

        Returns:
            int: The number of tokens, which is 4.
        """
        # 4 tokens:
        # <line: uint>, nload, <table_idx_dst: uint>, <spad_src: uint>
        # No HBM variant:
        # <line: uint>, nload, <table_idx_dst: uint>, <spad_var_name: uint>
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "nload".
        """
        return "nload"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `nload` CInstruction.

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
