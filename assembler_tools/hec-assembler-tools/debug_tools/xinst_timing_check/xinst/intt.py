from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents an `intt` instruction, inheriting from XInstruction.
    
    The Inverse Number Theoretic Transform (iNTT), converts NTT form to positional form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_intt.md
    """

    @classmethod
    def fromASMISALine(cls, line: str) -> list:
        """
        Parses an ASM ISA line to create an Instruction object.

        Parameters:
            line (str): The line of text to parse.

        Returns:
            list: An Instruction object if parsing is successful, None otherwise.

        Raises:
            ValueError: If the line cannot be parsed into an Instruction.
        """
        retval = None
        tokens = XInstruction.tokenizeFromASMISALine(cls.name, line)
        if tokens:
            tokens, comment = tokens
            if len(tokens) < 3 or tokens[2] != cls.name:
                raise ValueError('`line`: could not parse f{cls.name} from specified line.')
            dst_src_map = XInstruction.parseASMISASourceDestsFromTokens(tokens, cls._OP_NUM_DESTS, cls._OP_NUM_SOURCES, 3)
            retval = cls(int(tokens[0][1:]), # Bundle
                         int(tokens[1]), # PISA instruction number
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
            str: The name of the instruction, which is "intt".
        """
        return "intt"

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
        Constructs a new Instruction object.

        Parameters:
            bundle (int): The bundle number.
            pisa_instr (int): The PISA instruction number.
            dsts (list): List of destination registers.
            srcs (list): List of source registers.
            throughput (int): The throughput of the instruction.
            latency (int): The latency of the instruction.
            other (list): Additional parameters for the instruction.
            comment (str): Optional comment for the instruction.
        """
        super().__init__(bundle, pisa_instr, dsts, srcs, throughput, latency, other, comment)