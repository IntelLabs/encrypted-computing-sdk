from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `xinstfetch` CInstruction.

    This instruction fetches instructions from the HBM and sends them to the XINST queue.

    For more information, check the `xinstfetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_xinstfetch.md

    Properties:
        dstXQueue: Gets or sets the destination in the XINST queue.
        srcHBM: Gets or sets the source in the HBM.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens required for the instruction.

        The `xinstfetch` instruction requires 4 tokens:
        <line: uint>, xinstfetch, <xq_dst:uint>, <hbm_src: uint>

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "xinstfetch".
        """
        return "xinstfetch"

    def __init__(self, tokens: list, comment: str = ""):
        """
        Constructs a new `xinstfetch` CInstruction.

        Args:
            tokens (list): A list of tokens representing the instruction.
            comment (str, optional): An optional comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the number of tokens is invalid or the instruction name is incorrect.
            NotImplementedError: If the `xinstfetch` CInstruction is not supported in the linker.
        """
        super().__init__(tokens, comment=comment)
        raise NotImplementedError('`xinstfetch` CInstruction is not currently supported in linker.')

    @property
    def dstXQueue(self) -> int:
        """
        Gets the destination in the XINST queue.

        Returns:
            int: The destination in the XINST queue.
        """
        return int(self.tokens[2])

    @dstXQueue.setter
    def dstXQueue(self, value: int):
        """
        Sets the destination in the XINST queue.

        Args:
            value (int): The destination value to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative value, but {value} received.')
        self.tokens[2] = str(value)

    @property
    def srcHBM(self) -> int:
        """
        Gets the source in the HBM.

        Returns:
            int: The source in the HBM.
        """
        return int(self.tokens[3])

    @srcHBM.setter
    def srcHBM(self, value: int):
        """
        Sets the source in the HBM.

        Args:
            value (int): The source value to set.

        Raises:
            ValueError: If the value is negative.
        """
        if value < 0:
            raise ValueError(f'`value`: expected non-negative value, but {value} received.')
        self.tokens[3] = str(value)