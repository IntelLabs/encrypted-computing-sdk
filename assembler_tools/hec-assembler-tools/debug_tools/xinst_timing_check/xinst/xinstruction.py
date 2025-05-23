import re
from assembler.common.decorators import *
from assembler.instructions import tokenizeFromLine

class XInstruction:

    # To be initialized from ASM ISA spec
    _OP_NUM_DESTS          : int
    _OP_NUM_SOURCES        : int
    _OP_DEFAULT_THROUGHPUT : int
    _OP_DEFAULT_LATENCY    : int

    @classmethod
    def SetNumTokens(cls, val):
        pass

    @classmethod
    def SetNumDests(cls, val):
        cls._OP_NUM_DESTS = val

    @classmethod
    def SetNumSources(cls, val):
        cls._OP_NUM_SOURCES = val

    @classmethod
    def SetDefaultThroughput(cls, val):
        cls._OP_DEFAULT_THROUGHPUT = val

    @classmethod
    def SetDefaultLatency(cls, val):
        cls._OP_DEFAULT_LATENCY = val

    # Static methods
    # --------------
    @staticmethod
    def tokenizeFromASMISALine(op_name: str, line: str) -> list:
        """
        Checks if the specified instruction can be parsed from the specified
        line and, if so, return the tokenized line.

        Parameters:
            op_name (str): Name of operation that should be contained in the line.
            line (str): Line to tokenize.

        Returns:
            tuple: A tuple containing tokens (tuple of strings) and comment (str).
                   None if instruction cannot be parsed from the line.
        """
        retval = None
        tokens, comment = tokenizeFromLine(line)
        if len(tokens) > 2 and tokens[2] == op_name:
            retval = (tokens, comment)
        return retval

    @staticmethod
    def parseASMISASourceDestsFromTokens(tokens: list, num_dests: int, num_sources: int, offset: int = 0) -> dict:
        """
        Parses the sources and destinations for an instruction, given sources and
        destinations in tokens in P-ISA format.

        Parameters:
            tokens (list): List of string tokens where each token corresponds to a destination or
                           a source for the instruction being parsed, in order.
            num_dests (int): Number of destinations for the instruction.
            num_sources (int): Number of sources for the instruction.
            offset (int): Offset in the list of tokens where to start parsing.

        Returns:
            dict: A dictionary with, at most, two keys: "src" and "dst", representing the parsed sources
                  and destinations for the instruction. The value for each key is a list of parsed
                  registers, where a register is of the form tuple(register: int, bank: int).

        Raises:
            ValueError: If an invalid register name is encountered.
        """
        retval = {}
        dst_start = offset
        dst_end = dst_start + num_dests
        dst = []
        for dst_tokens in tokens[dst_start:dst_end]:
            if not re.search("r[0-9]+b[0-3]", dst_tokens):
                raise ValueError(f'Invalid register name: `{dst_tokens}`.')
            # Parse rXXbXX into a tuple of the form (reg, bank)
            tmp = dst_tokens[1:]
            reg = tuple(map(int, tmp.split('b')))
            dst.append(reg)
        src_start = dst_end
        src_end = src_start + num_sources
        src = []
        for src_tokens in tokens[src_start:src_end]:
            if not re.search("r[0-9]+b[0-3]", src_tokens):
                raise ValueError(f'Invalid register name: `{src_tokens}`.')
            # Parse rXXbXX into a tuple of the form (reg, bank)
            tmp = src_tokens[1:]
            reg = tuple(map(int, tmp.split('b')))
            src.append(reg)
        if dst:
            retval["dst"] = dst
        if src:
            retval["src"] = src
        return retval

    @classproperty
    def name(cls) -> str:
        """
        Gets the name for the instruction.

        Returns:
            str: The name of the instruction.
        """
        return cls._get_name()

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name for the instruction.

        Raises:
            NotImplementedError: If the method is not implemented in a derived class.
        """
        raise NotImplementedError('Abstract base')

    # Constructor
    # -----------

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
        Initializes an XInstruction object.

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
        self.bundle = bundle
        self.pisa_instr = pisa_instr
        self.srcs = srcs
        self.dsts = dsts
        self.throughput = throughput
        self.latency = latency
        self.other = other
        self.comment = comment

    def __str__(self):
        """
        Gets the string representation of the XInstruction.

        Returns:
            str: The string representation of the instruction.
        """
        retval = "f{}, {}, {}".format(self.bundle,
                                      self.pisa_instr,
                                      self.name)
        if self.dsts:
            dsts = ['r{}b{}'.format(r, b) for r, b in self.dsts]
            retval += ', {}'.format(', '.join(dsts))
        if self.srcs:
            srcs = ['r{}b{}'.format(r, b) for r, b in self.srcs]
            retval += ', {}'.format(', '.join(srcs))
        if self.other:
            retval += ', {}'.format(', '.join(self.other))
        if self.comment:
            retval += f' # {self.comment}'

        return retval