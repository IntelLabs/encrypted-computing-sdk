from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Encapsulates an `ntt` XInstruction (Number Theoretic Transform).
    Converts positional form to NTT form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_ntt.md
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `ntt` instruction requires 10 tokens:
        F<bundle_idx: uint>, <info: str>, ntt, <dst_top: str>, <dest_bot: str>, <src_top: str>, <src_bot: str>, <src_tw: str>, <stage: uint>, <res: uint>

        Returns:
            int: The number of tokens, which is 10.
        """
        return 10

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "ntt".
        """
        return "ntt"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `ntt` XInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
        """
        super().__init__(tokens, comment=comment)