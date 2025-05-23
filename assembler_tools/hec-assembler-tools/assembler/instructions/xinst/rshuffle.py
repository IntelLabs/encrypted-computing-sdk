import warnings
from argparse import Namespace

from assembler.common.cycle_tracking import CycleType
from assembler.common.decorators import *
from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable
from . import irshuffle

class Instruction(XInstruction):
    """
    Encapsulates an `rshuffle` XInstruction.

    Methods:
        SpecialLatency: Returns the special latency for rshuffle instructions.
        SpecialLatencyMax: Returns the maximum special latency for rshuffle instructions.
        SpecialLatencyIncrement: Returns the increment for special latency for rshuffle instructions.
        RSHUFFLE_DATA_TYPE: Returns the data type for rshuffle instructions.
        parseFromPISALine: Parses an `rshuffle` instruction from a pre-processed Kernel instruction string.
        set_irshuffleGlobalCycleReady: Sets the global cycle ready based on the last irshuffle.
        reset_GlobalCycleReady: Resets the global cycle ready for rshuffle and irshuffle instructions.
    """

    # To be initialized from ASM ISA spec
    _OP_NUM_TOKENS       : int
    _OP_RMOVE_LATENCY    : int
    _OP_RMOVE_LATENCY_MAX: int
    _OP_RMOVE_LATENCY_INC: int

    __rshuffle_global_cycle_ready = CycleType(0, 0) # Private class attribute to track cycle ready among rshuffles
    __irshuffle_global_cycle_ready = CycleType(0, 0) # Private class attribute to track the cycle ready based on last irshuffle

    @classmethod
    def isa_spec_as_dict(cls) -> dict:
        """
        Returns isa_spec attributes as dictionary.
        """
        dict = super().isa_spec_as_dict()
        dict.update({"num_tokens": cls._OP_NUM_TOKENS,
                     "special_latency_max": cls._OP_RMOVE_LATENCY_MAX,
                     "special_latency_increment": cls._OP_RMOVE_LATENCY_INC})
        return dict
    
    @classmethod
    def SetNumTokens(cls, val):
        cls._OP_NUM_TOKENS = val

    @classmethod
    def SetSpecialLatencyMax(cls, val):
        cls._OP_RMOVE_LATENCY_MAX = val

    @classmethod
    def SetSpecialLatencyIncrement(cls, val):
        cls._OP_RMOVE_LATENCY_INC = val
        cls._OP_RMOVE_LATENCY = cls._OP_RMOVE_LATENCY_INC

    @classproperty
    def SpecialLatency(cls):
        """
        Special latency (indicates the first increment at which another rshuffle instruction
        can be scheduled within `SpecialLatencyMax` latency).

        Returns:
            int: The special latency for rshuffle instructions.
        """
        return cls._OP_RMOVE_LATENCY

    @classproperty
    def SpecialLatencyMax(cls):
        """
        Special latency maximum (cannot enqueue any other rshuffle instruction within this latency
        unless it is in `SpecialLatencyIncrement`).

        Returns:
            int: The maximum special latency for rshuffle instructions.
        """
        return cls._OP_RMOVE_LATENCY_MAX

    @classproperty
    def SpecialLatencyIncrement(cls):
        """
        Special latency increment (can only enqueue any other rshuffle instruction
        within `SpecialLatencyMax` only in increments of this value).

        Returns:
            int: The increment for special latency for rshuffle instructions.
        """
        return cls._OP_RMOVE_LATENCY_INC

    @classproperty
    def RSHUFFLE_DATA_TYPE(cls):
        """
        Returns the data type for rshuffle instructions.

        Returns:
            str: The data type for rshuffle instructions, which is "ntt".
        """
        return "ntt"

    @classmethod
    def parseFromPISALine(cls, line: str) -> object:
        """
        Parses an `rshuffle` instruction from a pre-processed Kernel instruction string.

        A preprocessed kernel contains the split implementation of original NTT into
        HERACLES equivalent rshuffle, ntt, twntt.

        Parameters:
            line (str): String containing the instruction to parse.
                        Instruction format: N, rshuffle, dst0, dst1, src0, src1, wait_cyc # comment
                        Comment is optional.

                        Example line:
                        "13, rshuffle, outtmp_9_0 (2), outtmp_9_2 (3), outtmp_9_0 (2), outtmp_9_2 (3), 0"

        Returns:
            Namespace: A namespace with the following attributes:
                N (int): Ring size = Log_2(PMD)
                op_name (str): Operation name ("rshuffle")
                dst (list of tuple): List of destinations of the form (variable_name, suggested_bank).
                                     This list has two elements for `rshuffle`.
                src (list of tuple): List of sources of the form (variable_name, suggested_bank).
                                     This list has two elements for `rshuffle`.
                comment (str): String with the comment attached to the line (empty string if no comment).

            None: If an `rshuffle` could not be parsed from the input.
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
            # Ignore "res", but make sure it exists (syntax)
            assert(instr_tokens[params_end] is not None)

            retval = Namespace(**retval)
            assert(retval.op_name == cls.OP_NAME_PISA)
        return retval

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'rshuffle'.
        """
        return "rshuffle"

    def __init__(self,
                 id: int,
                 N: int,
                 dst: list,
                 src: list,
                 wait_cyc: int = 0,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `rshuffle` XInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            N (int): Ring size for the operation, Log_2(PMD).
            dst (list of Variable): List of destination variables.
            src (list of Variable): List of source variables.
            wait_cyc (int, optional): The number of wait cycles. Defaults to 0.
            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.
            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.
            comment (str, optional): A comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `latency` is less than the special latency for rshuffle instructions.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        if latency < Instruction._OP_RMOVE_LATENCY:
            raise ValueError((f'`latency`: expected a value greater than or equal to '
                              '{Instruction._OP_RMOVE_LATENCY}, but {latency} received.'))

        super().__init__(id, N, throughput, latency, comment=comment)

        self.wait_cyc = wait_cyc
        self._set_dests(dst)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, destinations, sources, and wait cycles.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'dst={}, src={}, '
                  'wait_cyc={})').format(type(self).__name__,
                                         self.name,
                                         hex(id(self)),
                                         self.id,
                                         self.dests,
                                         self.sources,
                                         self.wait_cyc)
        return retval

    @classmethod
    def __set_rshuffleGlobalCycleReady(cls, value: CycleType):
        """
        Sets the global cycle ready for rshuffle instructions.

        Parameters:
            value (CycleType): The cycle type value to set.
        """
        if (value > cls.__rshuffle_global_cycle_ready):
            cls.__rshuffle_global_cycle_ready = value

    @classmethod
    def set_irshuffleGlobalCycleReady(cls, value: CycleType):
        """
        Sets the global cycle ready based on the last irshuffle.

        Parameters:
            value (CycleType): The cycle type value to set.
        """
        if (value > cls.__irshuffle_global_cycle_ready):
            cls.__irshuffle_global_cycle_ready = value

    @classmethod
    def reset_GlobalCycleReady(cls, value=CycleType(0, 0)):
        """
        Resets the global cycle ready for rshuffle and irshuffle instructions.

        Parameters:
            value (CycleType, optional): The cycle type value to reset to. Defaults to CycleType(0, 0).
        """
        cls.__rshuffle_global_cycle_ready = value
        cls.__irshuffle_global_cycle_ready = value

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): A list of `Variable` objects to set as destinations.

        Raises:
            ValueError: If the number of destinations is incorrect or if the list does not contain `Variable` objects.
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
            value (list): A list of `Variable` objects to set as sources.

        Raises:
            ValueError: If the number of sources is incorrect or if the list does not contain `Variable` objects.
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
            CycleType: The maximum cycle ready among this instruction's sources and the global cycles-ready for other rshuffles and irshuffles.
        """
        # This will return the maximum cycle ready among this instruction
        # sources and the global cycles-ready for other rshuffles and other irshuffles.
        # An rshuffle cannot be within _OP_RMOVE_LATENCY cycles from another rshuffle,
        # nor within _OP_DEFAULT_LATENCY cycles from another irshuffle.
        return max(super()._get_cycle_ready(),
                   Instruction.__irshuffle_global_cycle_ready,
                   Instruction.__rshuffle_global_cycle_ready)

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        The ready cycle for all destinations is updated based on input `cycle_count` and
        this instruction latency. The global `rshuffle` ready cycle is also updated.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: The instruction is not ready to execute yet. Based on current cycle,
                          the instruction is ready to execute if its cycle_ready value is less than or
                          equal to `cycle_count`.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        original_throughput = super()._schedule(cycle_count, schedule_id)
        retval = self.throughput + self.wait_cyc
        assert(original_throughput <= retval)
        Instruction.__set_rshuffleGlobalCycleReady(CycleType(cycle_count.bundle, cycle_count.cycle + Instruction._OP_RMOVE_LATENCY))
        # Avoid rshuffles and irshuffles in the same bundle
        irshuffle.Instruction.set_rshuffleGlobalCycleReady(CycleType(cycle_count.bundle + 1, 0))
        return retval

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

        # N, rshuffle, dst0, dst1, src0, src1, res=0 # comment
        return super()._toPISAFormat(0)

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

        # id[0], N, op, dst_register0, dst_register1, src_register0, src_register1, wait_cycle, data_type="ntt", res=0 [# comment]
        return super()._toXASMISAFormat(self.wait_cyc, self.RSHUFFLE_DATA_TYPE)