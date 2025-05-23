from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents a `mul` Instruction.

    This instructions performs element-wise polynomial multiplication.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_mul.md
    
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
            if len(tokens) < 3 or tokens[2] != cls.name:
                raise ValueError('`line`: could not parse f{cls.name} from specified line.')
            dst_src_map = XInstruction.parseASMISASourceDestsFromTokens(tokens, cls._OP_NUM_DESTS, cls._OP_NUM_SOURCES, 3)
            retval = cls(int(tokens[0][1:]), # Bundle
                         int(tokens[1]), # Pisa
                         dst_src_map['dst'],
                         dst_src_map['src'],
                         cls._OP_DEFAULT_THROUGHPUT,
                         cls._OP_DEFAULT_LATENCY,
                         tokens[3 + cls._OP_NUM_DESTS + cls._OP_NUM_SOURCES:],
                         comment)
        return retval

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction, which is "mul".
        """
        return "mul"

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