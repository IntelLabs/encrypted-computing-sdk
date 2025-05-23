import warnings

from argparse import Namespace

from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable

class Instruction(XInstruction):
    """
    Represents an `add` instruction in the assembler with specific properties and methods for parsing,
    scheduling, and formatting.

    This instructions adds two polynomials stored in the register file and
    store the result in a register.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_add.md

    Methods:
        parseFromPISALine(line: str) -> list:
            Parses an `add` instruction from a Kernel instruction string.
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
    def parseFromPISALine(cls, line: str) -> list:
        """
        Parses an `add` instruction from a Kernel instruction string.

        Parameters:
            line (str): String containing the instruction to parse.
                Instruction format: N, add, dst (bank), src0 (bank), src1 (bank), res # comment
                Comment is optional.

                Example line:
                "13, add , output_0_1_3 (2), c_0_1_3 (0), d_0_1_3 (1), 1"

        Returns:
            Namespace: A namespace with the following attributes:
                N (int): Ring size = Log_2(PMD)
                op_name (str): Operation name ("add")
                dst (list[(str, int)]): List of destinations of the form (variable_name, suggested_bank).
                    This list has a single element for `add`.
                src (list[(str, int)]): List of sources of the form (variable_name, suggested_bank).
                    This list has two elements for `add`.
                res (int): Residual for the operation.
                comment (str): String with the comment attached to the line (empty string if no comment).
        """
        retval = None
        tokens = XInstruction.tokenizeFromPISALine(cls.OP_NAME_PISA, line)
        if tokens:
            retval = { "comment": tokens[1] }
            instr_tokens = tokens[0]
            if len(instr_tokens) > cls._OP_NUM_TOKENS:
                warnings.warn(f'Extra tokens detected for instruction "{cls.OP_NAME_PISA}"', SyntaxWarning)

            retval["N"] = int(instr_tokens[0])
            retval["op_name"] = instr_tokens[1]
            params_start = 2
            params_end = params_start + cls._OP_NUM_DESTS + cls._OP_NUM_SOURCES
            dst_src = cls.parsePISASourceDestsFromTokens(instr_tokens,
                                                         cls._OP_NUM_DESTS,
                                                         cls._OP_NUM_SOURCES,
                                                         params_start)
            retval.update(dst_src)
            retval["res"] = int(instr_tokens[params_end])

            retval = Namespace(**retval)
            assert(retval.op_name == cls.OP_NAME_PISA)
        return retval

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: ASM format operation.
        """
        return "add"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 res: int,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Initializes an Instruction object with the given parameters.

        Parameters:
            id (int): The unique identifier for the instruction.
            N (int): The ring size, typically Log_2(PMD).
            dst (list): List of destination variables.
            src (list): List of source variables.
            res (int): The residual for the operation.
            throughput (int, optional): The throughput of the instruction. Defaults to None.
            latency (int, optional): The latency of the instruction. Defaults to None.
            comment (str, optional): A comment associated with the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        super().__init__(id, N, throughput, latency, res=res, comment=comment)

        self._set_dests(dst)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of object.
        """
        retval=('<{}({}) object at {}>(id={}[0], res={}, '
                  'dst={}, src={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.res,
                                                           self.dests,
                                                           self.sources,
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): List of destination variables.

        Raises:
            ValueError: If the list does not contain the expected number of `Variable` objects.
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
            value (list): List of source variables.

        Raises:
            ValueError: If the list does not contain the expected number of `Variable` objects.
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
            *extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: Kernel format instruction.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toPISAFormat()

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            *extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: ASM format instruction.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toXASMISAFormat()