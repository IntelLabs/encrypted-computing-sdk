from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents a `nop` Instruction.

    This instruction adds a desired amount of idle cycles to the compute flow.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_nop.md

    Methods:
        fromASMISALine: Parses an ASM ISA line to create an Instruction instance.
    """
    
    @classmethod
    def fromASMISALine(cls, line: str) -> list:
        """
        Parses an ASM ISA line to create an Instruction instance.

        Args:
            line (str): The ASM ISA line to parse.

        Returns:
            list: A list containing the parsed Instruction instance.

        Raises:
            ValueError: If the line cannot be parsed into the expected format.
        """
        retval = None
        tokens = XInstruction.tokenizeFromASMISALine(cls.name, line)
        if tokens:
            tokens, comment = tokens
            if len(tokens) < 4 or tokens[2] != cls.name:
                raise ValueError('`line`: could not parse f{cls.name} from specified line.')
            idle_cycles = int(tokens[3]) + 1
            retval = cls(
                int(tokens[0][1:]),  # Bundle
                int(tokens[1]),  # Pisa
                [],
                [],
                idle_cycles,
                idle_cycles,
                tokens[3:],
                comment
            )
        return retval

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "nop".
        """
        return "nop"

    def __init__(self,
                 bundle: int,
                 pisa_instr: int,
                 dsts: list,
                 srcs: list,
                 throughput: int,
                 latency: int,
                 other: list = [],
                 comment: str = ""):
        """
        Initializes an Instruction instance.

        Args:
            bundle (int): The bundle identifier.
            pisa_instr (int): The PISA instruction identifier.
            dsts (list): The list of destination operands.
            srcs (list): The list of source operands.
            throughput (int): The throughput of the instruction.
            latency (int): The latency of the instruction.
            other (list, optional): Additional parameters. Defaults to an empty list.
            comment (str, optional): A comment associated with the instruction. Defaults to an empty string.
        """
        super().__init__(bundle, pisa_instr, dsts, srcs, throughput, latency, other, comment)