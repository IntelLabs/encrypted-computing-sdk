import warnings

from argparse import Namespace

from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable

class Instruction(XInstruction):
    """
    Represents an `ntt` (Number Theoretic Transform) instruction in an assembly language.

    This class is responsible for parsing, representing, and converting `ntt` instructions
    according to a specific instruction set architecture (ISA) specification.

    For more information, check the `ntt` specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_ntt.md

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
    def parseFromPISALine(cls, line: str) -> object:
        """
        Parses an 'ntt' instruction from a pre-processed Kernel instruction string.

        A preprocessed kernel contains the split implementation of the original NTT into
        HERACLES equivalent rshuffle, ntt, twntt.

        Parameters:
            line (str): String containing the instruction to parse.
                Instruction format: N, ntt, dst_top, dest_bot, src_top, src_bot, src_tw, stage, res # comment
                Comment is optional.

                Example line:
                "15, ntt, outtmp_9_0 (2), outtmp_9_2 (3), output_9_0 (2), output_9_1 (3), w_gen_17_1 (1), 1, 9"

        Returns:
            Namespace: A namespace with the following attributes:
                - N (int): Ring size = Log_2(PMD)
                - op_name (str): Operation name ("ntt")
                - dst (list of tuples): List of destinations of the form (variable_name, suggested_bank).
                    This list has two elements for 'ntt'.
                - src (list of tuples): List of sources of the form (variable_name, suggested_bank).
                    This list has three elements for 'ntt'.
                - stage (int): Stage number of the current NTT instruction.
                - res (int): Residual for the operation.
                - comment (str): String with the comment attached to the line (empty string if no comment).

            Returns None if an 'ntt' could not be parsed from the input.
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
            params_end = params_start + cls._OP_NUM_DESTS + cls._OP_NUM_SOURCES
            dst_src = cls.parsePISASourceDestsFromTokens(instr_tokens,
                                                         cls._OP_NUM_DESTS,
                                                         cls._OP_NUM_SOURCES,
                                                         params_start)
            retval.update(dst_src)
            retval["stage"] = int(instr_tokens[params_end])
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
        return "ntt"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 stage: int,
                 res: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Initializes an Instruction object.

        Parameters:
            id (int): The unique identifier for the instruction.
            N (int): The ring size.
            dst (list): List of destination variables.
            src (list): List of source variables.
            stage (int): The stage number of the instruction.
            res (int): The residual for the operation.
            throughput (int, optional): The throughput of the instruction. Defaults to the class-level default if not provided.
            latency (int, optional): The latency of the instruction. Defaults to the class-level default if not provided.
            comment (str, optional): An optional comment for the instruction.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        super().__init__(id, N, throughput, latency, res=res, comment=comment)

        self.__stage = stage  # (Read-only) stage
        self._set_dests(dst)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the object.
        """
        retval = ('<{}({}) object at {}>(id={}[0], res={}, '
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

    @property
    def stage(self):
        """
        Returns the stage of the instruction.

        Returns:
            int: The stage as an integer.
        """
        return self.__stage

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
        if extra_args:
            raise ValueError('`extra_args` not supported.')

        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)
        # N, ntt, dst_top (bank), dest_bot (bank), src_top (bank), src_bot (bank), src_tw (bank), stage, res # comment
        retval = super()._toPISAFormat(self.stage)

        return retval

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

        return super()._toXASMISAFormat(self.stage)