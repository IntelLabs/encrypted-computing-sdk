import warnings

from argparse import Namespace

from assembler.common.cycle_tracking import CycleType
from assembler.common.decorators import *
from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable
from . import rshuffle

class Instruction(XInstruction):
    """
    Represents an instruction in the assembler with specific properties and methods for parsing,
    scheduling, and formatting. This class is specifically designed to handle `irshuffle` 
    instruction within the assembler's instruction set architecture (ISA).

    Attributes:
        SpecialLatency (int): Special latency indicating the first increment at which another rshuffle instruction
            can be scheduled within `SpecialLatencyMax` latency.
        SpecialLatencyMax (int): Special latency maximum, indicating that no other rshuffle instruction can be enqueued
            within this latency unless it is in `SpecialLatencyIncrement`.
        SpecialLatencyIncrement (int): Special latency increment, allowing enqueuing of other rshuffle instructions within
            `SpecialLatencyMax` only in increments of this value.
        RSHUFFLE_DATA_TYPE (str): Data type used for irshuffle operations, default is "intt".

    Methods:
        parseFromPISALine(line: str) -> object:
            Parses an `irshuffle` instruction from a pre-processed P-ISA Kernel instruction string.
    """

    # To be initialized from ASM ISA spec
    _OP_NUM_TOKENS        : int
    _OP_IRMOVE_LATENCY    : int
    _OP_IRMOVE_LATENCY_MAX: int
    _OP_IRMOVE_LATENCY_INC: int

    __irshuffle_global_cycle_ready = CycleType(0, 0) # private class attribute to track cycle ready among irshuffles
    __rshuffle_global_cycle_ready = CycleType(0, 0) # private class attribute to track the cycle ready based on last rshuffle

    @classmethod
    def isa_spec_as_dict(cls) -> dict:
        """
        Returns isa_spec attributes as dictionary.
        """
        dict = super().isa_spec_as_dict()
        dict.update({"num_tokens": cls._OP_NUM_TOKENS,
                     "special_latency_max": cls._OP_IRMOVE_LATENCY_MAX,
                     "special_latency_increment": cls._OP_IRMOVE_LATENCY_INC})
        return dict

    @classmethod
    def SetNumTokens(cls, val):
        cls._OP_NUM_TOKENS = val

    @classmethod
    def SetSpecialLatencyMax(cls, val):
        cls._OP_IRMOVE_LATENCY_MAX = val

    @classmethod
    def SetSpecialLatencyIncrement(cls, val):
        cls._OP_IRMOVE_LATENCY_INC = val
        cls._OP_IRMOVE_LATENCY = cls._OP_IRMOVE_LATENCY_INC

    @classproperty
    def SpecialLatency(cls):
        """
        Special latency (indicates the first increment at which another rshuffle instruction
        can be scheduled within `SpecialLatencyMax` latency).

        Returns:
            int: The special latency value.
        """
        return cls._OP_IRMOVE_LATENCY

    @classproperty
    def SpecialLatencyMax(cls):
        """
        Special latency maximum (cannot enqueue any other rshuffle instruction within this latency
        unless it is in `SpecialLatencyIncrement`).

        Returns:
            int: The special latency maximum value.
        """
        return cls._OP_IRMOVE_LATENCY_MAX

    @classproperty
    def SpecialLatencyIncrement(cls):
        """
        Special latency increment (can only enqueue any other rshuffle instruction  # TCHECK for rshuffle
        within `SpecialLatencyMax` only in increments of this value).

        Returns:
            int: The special latency increment value.
        """
        return cls._OP_IRMOVE_LATENCY_INC

    @classproperty
    def RSHUFFLE_DATA_TYPE(cls):
        """
        Data type used for rshuffle operations.

        Returns:
            str: The data type, default is "intt".
        """
        return "intt"

    @classmethod
    def parseFromPISALine(cls, line: str) -> object:
        """
        Parses an `irshuffle` instruction from a pre-processed P-ISA Kernel instruction string.

        A preprocessed kernel contains the split implementation of original iNTT into
        HERACLES equivalent irshuffle, intt, twintt.

        Parameters:
            line (str): String containing the instruction to parse.
                Instruction format: N, irshuffle, dst0, dst1, src0, src1, res # comment
                Comment is optional.

                Example line:
                "13, irshuffle, outtmp_9_0 (2), outtmp_9_2 (3), outtmp_9_0 (2), outtmp_9_2 (3), 0"

        Returns:
            Namespace: A namespace with the following attributes:
                - N (int): Ring size = Log_2(PMD)
                - op_name (str): Operation name ("irshuffle")
                - dst (list[(str, int)]): List of destinations of the form (variable_name, suggested_bank).
                    This list has two elements for `irshuffle`.
                - src (list[(str, int)]): List of sources of the form (variable_name, suggested_bank).
                    This list has two elements for `irshuffle`.
                - comment (str): String with the comment attached to the line (empty string if no comment).

            Returns None if an `irshuffle` could not be parsed from the input.
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
            # ignore "res", but make sure it exists (syntax)
            assert(instr_tokens[params_end] is not None)

            retval = Namespace(**retval)
            assert(retval.op_name == cls.OP_NAME_PISA)
        return retval

    @classmethod
    def _get_name(cls) -> str:
        """
        Returns the operation name in PISA format.

        Returns:
            str: The operation name in PISA format.
        """
        return cls.OP_NAME_PISA

    @classmethod
    def _get_OP_NAME_PISA(cls) -> str:
        """
        Returns the operation name in PISA format.

        Returns:
            str: The operation name in PISA format.
        """
        return "irshuffle"

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: The operation name in ASM format.
        """
        return "rshuffle"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 wait_cyc: int = 0,
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
            wait_cyc (int, optional): The wait cycle for the instruction. Defaults to 0.
            throughput (int, optional): The throughput of the instruction. Defaults to None.
            latency (int, optional): The latency of the instruction. Defaults to None.
            comment (str, optional): A comment associated with the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the latency is less than the special latency.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        if latency < Instruction._OP_IRMOVE_LATENCY:
            raise ValueError((f'`latency`: expected a value greater than or equal to '
                              '{Instruction._OP_IRMOVE_LATENCY}, but {latency} received.'))

        super().__init__(id, N, throughput, latency, comment=comment)

        self.wait_cyc = wait_cyc
        self._set_dests(dst)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'dst={}, src={}, '
                  'wait_cyc={}, res={})').format(type(self).__name__,
                                                 self.name,
                                                 hex(id(self)),
                                                 self.id,
                                                 self.dests,
                                                 self.sources,
                                                 self.wait_cyc,
                                                 self.res)
        return retval

    @classmethod
    def __set_irshuffleGlobalCycleReady(cls, value: CycleType):
        """
        Sets the global cycle ready for irshuffle instructions.

        Parameters:
            value (CycleType): The cycle type value to set.
        """
        if (value > cls.__irshuffle_global_cycle_ready):
            cls.__irshuffle_global_cycle_ready = value

    @classmethod
    def set_rshuffleGlobalCycleReady(cls, value: CycleType):
        """
        Sets the global cycle ready for rshuffle instructions.

        Parameters:
            value (CycleType): The cycle type value to set.
        """
        if (value > cls.__rshuffle_global_cycle_ready):
            cls.__rshuffle_global_cycle_ready = value

    @classmethod
    def reset_GlobalCycleReady(cls, value = CycleType(0, 0)):
        """
        Resets the global cycle ready for both irshuffle and rshuffle instructions.

        Parameters:
            value (CycleType, optional): The cycle type value to reset to. Defaults to CycleType(0, 0).
        """
        cls.__rshuffle_global_cycle_ready = value
        cls.__irshuffle_global_cycle_ready = value

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): List of destination variables.

        Raises:
            ValueError: If the list does not contain the expected number of Variable objects.
        """
        if len(value) != Instruction._OP_NUM_DESTS:
            raise ValueError((f"`value`: Expected list of {Instruction._OP_NUM_DESTS} Variable objects, "
                              "but list with {len(value)} elements received."))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of Variable objects.")
        super()._set_dests(value)

    def _set_sources(self, value):
        """
        Sets the source variables for the instruction.

        Parameters:
            value (list): List of source variables.

        Raises:
            ValueError: If the list does not contain the expected number of Variable objects.
        """
        if len(value) != Instruction._OP_NUM_SOURCES:
            raise ValueError((f"`value`: Expected list of {Instruction._OP_NUM_SOURCES} Variable objects, "
                              "but list with {len(value)} elements received."))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of Variable objects.")
        super()._set_sources(value)

    def _get_cycle_ready(self):
        """
        Returns the current value for ready cycle.

        Overrides :func:`BaseInstruction._get_cycle_ready`.

        Returns:
            CycleType: The current cycle ready value.
        """
        # This will return the maximum cycle ready among this instruction
        # sources and the global cycles-ready for other rshuffles and other irshuffles.
        # An irshuffle cannot be within _OP_IRMOVE_LATENCY cycles from another irshuffle,
        # nor within _OP_DEFAULT_LATENCY cycles from another rshuffle.
        return max(super()._get_cycle_ready(),
                   Instruction.__irshuffle_global_cycle_ready,
                   Instruction.__rshuffle_global_cycle_ready)

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        The ready cycle for all destinations is updated based on input `cycle_count` and
        this instruction latency. The global `xrshuffle` ready cycles is also updated.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_id (int): The schedule identifier.

        Raises:
            RuntimeError: If the instruction is not ready to execute yet. Based on current cycle,
                the instruction is ready to execute if its cycle_ready value is less than or
                equal to `cycle_count`.

        Returns:
            int: The throughput for this instruction, i.e., the number of cycles by which to advance
                the current cycle counter.
        """
        original_throughput = super()._schedule(cycle_count, schedule_id)
        retval = self.throughput + self.wait_cyc
        assert(original_throughput <= retval)
        Instruction.__set_irshuffleGlobalCycleReady(CycleType(cycle_count.bundle, cycle_count.cycle + Instruction._OP_IRMOVE_LATENCY))
        # Avoid rshuffles and irshuffles in the same bundle
        rshuffle.Instruction.set_irshuffleGlobalCycleReady(CycleType(cycle_count.bundle + 1, 0))
        return retval

    def _toPISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to kernel format.

        Parameters:
            *extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: The instruction in kernel format.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # N, irshuffle, dst0, dst1, src0, src1, res=0 # comment
        return super()._toPISAFormat(0)

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            *extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: The instruction in ASM format.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # id[0], N, op, dst_register0, dst_register1, src_register0, src_register1, wait_cycle, data_type="intt", res=0 [# comment]
        return super()._toXASMISAFormat(self.wait_cyc, self.RSHUFFLE_DATA_TYPE)