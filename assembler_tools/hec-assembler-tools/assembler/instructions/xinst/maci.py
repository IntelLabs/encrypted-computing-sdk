import warnings

from argparse import Namespace

from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable

class Instruction(XInstruction):
    """
    Represents a `maci` (multiply-accumulate immediate) instruction in an assembly language.
    
    This class is responsible for parsing, representing, and converting 'maci' instructions
    according to a specific instruction set architecture (ISA) specification.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_maci.md
    """

    # To be initialized from ASM ISA spec
    _OP_NUM_TOKENS: int

    @classmethod
    def isa_spec_as_dict(cls) -> dict:
        """
        Returns isa_spec attributes as dictionary.
        """
        dict = super().isa_spec_as_dict()
        dict.update({"num_tokens": cls._OP_NUM_TOKENS})
        return dict

    @classmethod
    def SetNumTokens(cls, val):
        cls._OP_NUM_TOKENS = val

    @classmethod
    def SetNumSources(cls, val):
        cls._OP_NUM_SOURCES = val
        # In ASM ISA spec there are 2 sources, but src[0] == dst
        cls._OP_NUM_PISA_SOURCES = cls._OP_NUM_SOURCES - 1
    
    @classmethod
    def parseFromPISALine(cls, line: str) -> list:
        """
        Parses a 'maci' instruction from a Kernel instruction string.

        Parameters:
            line (str): 
                String containing the instruction to parse.
                Instruction format: N, maci, dst (bank), src (bank), imm, res # comment
                Comment is optional.

                Example line:
                "13, maci, coeff_0_1_3 (2), c2_4_3 (3), Qqr_extend_2_13_4, 13"

        Returns:
            list: 
                A list of tuples with a single element representing the parsed information,
                or an empty list if a 'maci' could not be parsed from the input.

                Element `Instruction` is this class.

                Element `parsed_op` is a namespace with the following attributes:
                - N (int): Ring size = Log_2(PMD)
                - op_name (str): Operation name ("maci")
                - dst (list of tuples): List of destinations of the form (variable_name, suggested_bank).
                This list has a single element for 'maci': dst[0] = dst[0] + src[0] * imm
                - src (list of tuples): List of sources of the form (variable_name, suggested_bank).
                This list has a single element for 'maci'.
                - imm (str): Name of immediate identifier. This will be replaced by a literal value during linkage.
                - res (int): Residual for the operation.
                - comment (str): String with the comment attached to the line (empty string if no comment).
        """
        retval = None
        tokens = XInstruction.tokenizeFromPISALine(cls.OP_NAME_PISA, line)
        if tokens:
            retval = {"comment": tokens[1]}
            instr_tokens = tokens[0]
            if len(instr_tokens) > cls._OP_NUM_TOKENS:
                warnings.warn(f'Extra tokens detected for instruction "{cls.OP_NAME_PISA}"', SyntaxWarning)

            retval["N"] = int(instr_tokens[0])
            retval["op_name"] = instr_tokens[1]
            params_start = 2
            params_end = params_start + cls._OP_NUM_DESTS + cls._OP_NUM_PISA_SOURCES
            dst_src = cls.parsePISASourceDestsFromTokens(instr_tokens,
                                                         cls._OP_NUM_DESTS,
                                                         cls._OP_NUM_PISA_SOURCES,
                                                         params_start)
            retval.update(dst_src)
            retval["imm"] = instr_tokens[params_end]
            retval["res"] = int(instr_tokens[params_end + 1])

            retval = Namespace(**retval)
            assert(retval.op_name == cls.OP_NAME_PISA)
        return retval

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: The operation name as a string.
        """
        return "maci"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 imm: str,
                 res: int,
                 comment: str = "",
                 throughput: int = None,
                 latency: int = None):
        """
        Initializes an Instruction object for a 'maci' operation.

        Parameters:
            id (int): 
                The unique identifier for the instruction.
            N (int): 
                The ring size.
            dst (list): 
                List of destination variables.
            src (list): 
                List of source variables.
            imm (str): 
                The immediate value identifier.
            res (int): 
                The residual for the operation.
            comment (str, optional): 
                An optional comment for the instruction.
            throughput (int, optional): 
                The throughput of the instruction. Defaults to the class-level default if not provided.
            latency (int, optional): 
                The latency of the instruction. Defaults to the class-level default if not provided.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        super().__init__(id, N, throughput, latency, res=res, comment=comment)

        self.__imm = imm  # (Read-only) immediate
        self._set_dests(dst)
        self._set_sources([self.dests[0]] + src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the object.
        """
        retval = ('<{}({}) object at {}>(id={}[0], res={}, imm={}, '
                  'dst={}, src={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                       self.name,
                                                       hex(id(self)),
                                                       self.id,
                                                       self.res,
                                                       self.imm,
                                                       self.dests,
                                                       self.sources,
                                                       self.throughput,
                                                       self.latency)
        return retval

    @property
    def imm(self):
        """
        Returns the immediate value identifier.

        Returns:
            str: The immediate value identifier.
        """
        return self.__imm

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): A list of Variable objects representing the destinations.

        Raises:
            ValueError: If the list does not contain the expected number of Variable objects.
        """
        if len(value) != Instruction._OP_NUM_DESTS:
            raise ValueError(("`value`: Expected list of {} Variable objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_DESTS,
                                                                           len(value))))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of Variable objects.")
        super()._set_dests(value)

    def _set_sources(self, value):
        """
        Sets the source variables for the instruction.

        Parameters:
            value (list): A list of Variable objects representing the sources.

        Raises:
            ValueError: If the list does not contain the expected number of Variable objects.
        """
        if len(value) != Instruction._OP_NUM_SOURCES:
            raise ValueError(("`value`: Expected list of {} Variable objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_SOURCES,
                                                                           len(value))))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of Variable objects.")
        super()._set_sources(value)

    def _toPISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to kernel format.

        Parameters:
            extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: The instruction in kernel format as a string.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # N, muli, dst (bank), src0 (bank), imm, res # comment
        preamble = (self.N,)
        extra_args = (self.imm,)
        extra_args = tuple(src.toPISAFormat() for src in self.sources[1:]) + extra_args
        extra_args = tuple(dst.toPISAFormat() for dst in self.dests) + extra_args
        if self.res is not None:
            extra_args += (self.res,)
        return self.toStringFormat(preamble,
                                   self.OP_NAME_PISA,
                                   *extra_args)

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: The instruction in ASM format as a string.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toXASMISAFormat(self.imm)