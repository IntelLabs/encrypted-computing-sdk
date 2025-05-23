from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents an Instruction with specific operational parameters and special latency properties.
    
    Methods:
        fromASMISALine: Parses an ASM ISA line to create an Instruction instance.
        _get_name: Gets the name of the instruction.

    Properties:
        data_type: Gets the data type from the 'other' parameters.
        wait_cycles: Gets the wait cycles from the 'other' parameters.
        special_latency_max: Gets the special latency maximum.
        special_latency_increment: Gets the special latency increment.
    """
    
    # To be initialized from ASM ISA spec
    _OP_RMOVE_LATENCY    : int
    _OP_RMOVE_LATENCY_MAX: int
    _OP_RMOVE_LATENCY_INC: int

    @classmethod
    def SetSpecialLatencyMax(cls, val):
        cls._OP_RMOVE_LATENCY_MAX = val
        cls._OP_RMOVE_LATENCY = cls._OP_RMOVE_LATENCY_MAX

    @classmethod
    def SetSpecialLatencyIncrement(cls, val):
        cls._OP_RMOVE_LATENCY_INC = val

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
            if len(tokens) < 9 or tokens[2] != cls.name:
                raise ValueError('`line`: could not parse f{cls.name} from specified line.')
            dst_src_map = XInstruction.parseASMISASourceDestsFromTokens(tokens, cls._OP_NUM_DESTS, cls._OP_NUM_SOURCES, 3)
            retval = cls(int(tokens[0][1:]), # bundle
                         int(tokens[1]), # pisa
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
            str: The name of the instruction, which is "rshuffle".
        """
        return "rshuffle"

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

        Raises:
            ValueError: If the 'other' list does not contain at least two parameters.
        """
        if len(other) < 2:
            raise ValueError('`other`: requires two parameters after sources.')
        super().__init__(bundle, pisa_instr, dsts, srcs, throughput + int(other[0]), latency, other, comment)

    @property
    def data_type(self):
        """
        Gets the data type from the 'other' parameters.

        Returns:
            The data type.
        """
        return self.other[1]

    @property
    def wait_cycles(self):
        """
        Gets the wait cycles from the 'other' parameters.

        Returns:
            The wait cycles.
        """
        return self.other[0]

    @property
    def special_latency_max(self):
        """
        Gets the special latency maximum.

        Returns:
            int: The special latency maximum.
        """
        return self._OP_RMOVE_LATENCY

    @property
    def special_latency_increment(self):
        """
        Gets the special latency increment.

        Returns:
            int: The special latency increment.
        """
        return self._OP_RMOVE_LATENCY_INC
