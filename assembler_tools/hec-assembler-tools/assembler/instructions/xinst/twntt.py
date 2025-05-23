import warnings

from argparse import Namespace

from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable

class Instruction(XInstruction):
    """
    Encapsulates a `twntt` XInstruction.

    This instruction performs on-die generation of twiddle factors for the next stage of NTT.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_twntt.md

    Attributes:
        tw_meta (int): Indexing information of the twiddle metadata.
        stage (int): Stage number of the current NTT instruction.
        block (int): Index of the current word in the 2-words (16KB) polynomial.

    Methods:
        parseFromPISALine: Parses a `twntt` instruction from a pre-processed Kernel instruction string.
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
        Parses a `twntt` instruction from a pre-processed Kernel instruction string.

        A preprocessed kernel contains the split implementation of original NTT into
        HERACLES equivalent rshuffle, ntt, twntt.

        Parameters:
            line (str): String containing the instruction to parse.
                        Instruction format: N, twntt, dst_tw, src_tw, tw_meta, stage, block, res # comment
                        Comment is optional.

                        Example line:
                        "15, twntt, w_gen_17_1 (1), w_gen_17_1 (1), 9, 300, 1, 0"

        Returns:
            Namespace: A namespace with the following attributes:
                N (int): Ring size = Log_2(PMD)
                op_name (str): Operation name ("twntt")
                dst (list of tuple): List of destinations of the form (variable_name, suggested_bank).
                                     This list has a single element for `twntt`.
                src (list of tuple): List of sources of the form (variable_name, suggested_bank).
                                     This list has a single element for `twntt`.
                tw_meta (int): Indexing information of the twiddle metadata.
                stage (int): Stage number of the current NTT instruction.
                block (int): Index of current word in the 2-words (16KB) polynomial.
                res (int): Residual for the operation.
                comment (str): String with the comment attached to the line (empty string if no comment).

            None: If a `twntt` could not be parsed from the input.
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
            retval["tw_meta"] = int(instr_tokens[params_end])
            retval["stage"] = int(instr_tokens[params_end + 1])
            retval["block"] = int(instr_tokens[params_end + 2])
            retval["res"] = int(instr_tokens[params_end + 3])

            retval = Namespace(**retval)
            assert(retval.op_name == cls.OP_NAME_PISA)
        return retval

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'twntt'.
        """
        return "twntt"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 tw_meta: int,
                 stage: int,
                 block: int,
                 res: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `twntt` XInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            N (int): Ring size for the operation, Log_2(PMD).

            dst (list of Variable): List of destination variables.

            src (list of Variable): List of source variables.

            tw_meta (int): Indexing information of the twiddle metadata.

            stage (int): Stage number of the current NTT instruction.

            block (int): Index of the current word in the 2-words (16KB) polynomial.

            res (int): Residual for the operation.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        super().__init__(id, N, throughput, latency, res=res, comment=comment)

        self.__tw_meta = tw_meta # (Read-only) tw_meta
        self.__stage = stage # (Read-only) stage
        self.__block = block # (Read-only) block
        self._set_dests(dst)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, residual, tw_meta, stage, block, destinations, sources, throughput, and latency.
        """
        retval=('<{}({}) object at {}>(id={}[0], res={}, tw_meta={}, stage={}, block={}, '
                  'dst={}, src={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.res,
                                                           self.tw_meta,
                                                           self.stage,
                                                           self.block,
                                                           self.dests,
                                                           self.sources,
                                                           self.throughput,
                                                           self.latency)
        return retval

    @property
    def tw_meta(self):
        """
        Returns the twiddle metadata index.

        Returns:
            int: The twiddle metadata index.
        """
        return self.__tw_meta

    @property
    def stage(self):
        """
        Returns the stage number of the current NTT instruction.

        Returns:
            int: The stage number.
        """
        return self.__stage

    @property
    def block(self):
        """
        Returns the index of the current word in the 2-words (16KB) polynomial.

        Returns:
            int: The block index.
        """
        return self.__block

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): A list of `Variable` objects to set as destinations.

        Raises:
            ValueError: If the number of destinations is incorrect or if the list does not contain `Variable` objects.
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
            value (list): A list of `Variable` objects to set as sources.

        Raises:
            ValueError: If the number of sources is incorrect or if the list does not contain `Variable` objects.
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
            extra_args: Additional arguments, which are not supported.

        Returns:
            str: The instruction in kernel format.

        Raises:
            ValueError: If extra arguments are provided.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # N, twntt, dst_tw, src_tw, tw_meta, stage, block, res # comment
        retval = super()._toPISAFormat(self.tw_meta,
                                       self.stage,
                                       self.block)
        return retval

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            extra_args: Additional arguments, which are not supported.

        Returns:
            str: The instruction in ASM format.

        Raises:
            ValueError: If extra arguments are provided.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toXASMISAFormat(self.tw_meta,
                                        self.stage,
                                        self.block,
                                        self.N)