from typing import final
from typing import NamedTuple

from assembler.common.config import GlobalConfig
from assembler.common.counter import Counter
from assembler.common.cycle_tracking import CycleTracker, CycleType
from assembler.common.decorators import *

class ScheduleTiming(NamedTuple):
    """
    A named tuple to add structure to schedule timing.

    Attributes:
        cycle (CycleType): The cycle in which the instruction was scheduled.
        index (int): The index for the instruction in its schedule listing.
    """
    cycle: CycleType
    index: int

class BaseInstruction(CycleTracker):
    """
    The base class for all instructions.

    This class encapsulates data regarding an instruction, as well as scheduling
    logic and functionality. It inherits members from the CycleTracker class.

    Class Properties:
        name (str): Returns the name of the represented operation.
        OP_NAME_ASM (str): ASM-ISA name for the instruction.
        OP_NAME_PISA (str): P-ISA name for the instruction.

    Class Methods:
        _get_name(cls) -> str: Derived classes should implement this method and return the correct
            name for the instruction. Defaults to the ASM-ISA name.
        _get_OP_NAME_ASM(cls) -> str: Derived classes should implement this method and return the correct
            ASM name for the operation. Default throws not implemented.
        _get_OP_NAME_PISA(cls) -> str: Derived classes should implement this method and return the correct
            P-ISA name for the operation. Defaults to the ASM-ISA name.

    Constructors:
        __init__(self, id: int, throughput: int, latency: int, comment: str = ""): 
            Initializes a new BaseInstruction object.

    Attributes:
        _dests (list[CycleTracker]): List of destination objects. Derived classes can override 
            _set_dests to validate this attribute.
        _frozen_cisa (str): Contains frozen CInst in ASM ISA format after scheduling. Empty string if not frozen.
        _frozen_misa (str): Contains frozen MInst in ASM ISA format after scheduling. Empty string if not frozen.
        _frozen_pisa (str): Contains frozen P-ISA format after scheduling. Empty string if not frozen.
        _frozen_xisa (str): Contains frozen XInst in ASM ISA format after scheduling. Empty string if not frozen.
        _sources (list[CycleTracker]): List of source objects. Derived classes can override 
            _set_sources to validate this attribute.
        comment (str): Comment for the instruction.

    Properties:
        dests (list): Gets or sets the list of destination objects. The elements of the list are derived dependent.
            Calls _set_dests to set value.
        id (tuple): Gets the unique instruction ID. This is a combination of the client ID specified during
            construction and a unique nonce per instruction.
        is_scheduled (bool): Returns whether the instruction has been scheduled (True) or not (False).
        latency (int): Returns the latency of the represented operation. This is the number
            of clock cycles before the results of the operation are ready in the destination.
        schedule_timing (ScheduleTiming): Gets the cycle and index in which this instruction was scheduled or 
            None if not scheduled yet. Index is subject to change and it is not final until the second pass of scheduling.
        sources (list): Gets or sets the list of source objects. The elements of the list are derived dependent.
            Calls _set_sources to set value.
        throughput (int): Returns the throughput of the represented operation. Number of clock cycles
            before a new instruction can be decoded/queued for execution.

    Magic Methods:
        __eq__(self, other): Checks equality between two BaseInstruction objects.
        __hash__(self): Returns the hash of the BaseInstruction object.
        __repr__(self): Returns a string representation of the BaseInstruction object.
        __str__(self): Returns a string representation of the BaseInstruction object.

    Methods:
        _schedule(self, cycle_count: CycleType, schedule_idx: int) -> int: 
            Schedules the instruction, simulating timings of executing this instruction. Derived
            classes should override with their scheduling functionality.
        _toCASMISAFormat(self, *extra_args) -> str: Converts the instruction to CInst ASM-ISA format. 
            Derived classes should override with their functionality.
        _toMASMISAFormat(self, *extra_args) -> str: Converts the instruction to MInst ASM-ISA format. 
            Derived classes should override with their functionality.
        _toPISAFormat(self, *extra_args) -> str: Converts the instruction to P-ISA kernel format. 
            Derived classes should override with their functionality.
        _toXASMISAFormat(self, *extra_args) -> str: Converts the instruction to XInst ASM-ISA format. 
            Derived classes should override with their functionality.
        freeze(self): Called immediately after _schedule() to freeze the instruction after scheduling
            to preserve the instruction string representation to output into the listing.
            Changes made to the instruction and its components after freezing are ignored.
        schedule(self, cycle_count: CycleType, schedule_idx: int) -> int: 
            Schedules and freezes the instruction, simulating timings of executing this instruction.
        toStringFormat(self, preamble, op_name: str, *extra_args) -> str: 
            Converts the instruction to a string format.
        toPISAFormat(self) -> str: Converts the instruction to P-ISA kernel format.
        toXASMISAFormat(self) -> str: Converts the instruction to ASM-ISA format.
        toCASMISAFormat(self) -> str: Converts the instruction to CInst ASM-ISA format.
        toMASMISAFormat(self) -> str: Converts the instruction to MInst ASM-ISA format.
    """
    # To be initialized from ASM ISA spec
    _OP_NUM_DESTS          : int
    _OP_NUM_SOURCES        : int
    _OP_DEFAULT_THROUGHPUT : int
    _OP_DEFAULT_LATENCY    : int

    __id_count = Counter.count(0) # internal unique sequence counter to generate unique IDs

    # Class methods and properties
    # ----------------------------
    @classmethod
    def isa_spec_as_dict(cls) -> dict:
        """
        Returns attributes as dictionary.
        """
        dict = {"num_dests": cls._OP_NUM_DESTS, 
                "num_sources": cls._OP_NUM_SOURCES,
                "default_throughput": cls._OP_DEFAULT_THROUGHPUT,
                "default_latency": cls._OP_DEFAULT_LATENCY}
        return dict
    
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

    @classproperty
    def name(cls) -> str:
        """
        Name for the instruction.
        """
        return cls._get_name()

    @classmethod
    def _get_name(cls) -> str:
        """
        Derived classes should implement this method and return correct
        name for the instruction. Defaults to the ASM-ISA name.
        """
        return cls.OP_NAME_ASM

    @classproperty
    def OP_NAME_PISA(cls) -> str:
        """
        P-ISA name for the instruction.
        """
        return cls._get_OP_NAME_PISA()

    @classmethod
    def _get_OP_NAME_PISA(cls) -> str:
        """
        Derived classes should implement this method and return correct
        P-ISA name for the operation. Defaults to the ASM-ISA name.
        """
        return cls.OP_NAME_ASM

    @classproperty
    def OP_NAME_ASM(cls) -> str:
        """
        ASM-ISA name for instruction.

        Will throw if no ASM-ISA name for instruction.
        """
        return cls._get_OP_NAME_ASM()

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Derived classes should implement this method and return correct
        ASM name for the operation.
        """
        raise NotImplementedError('Abstract method not implemented.')

    # Constructor
    # -----------

    def __init__(self,
                 id: int,
                 throughput : int,
                 latency : int,
                 comment: str = ""):
        """
        Initializes a new BaseInstruction object.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            throughput (int): Number of clock cycles that it takes after this instruction starts executing before the
                execution engine can start executing a new instruction. Instructions are pipelined, so,
                another instruction can be started in the clock cycle after this instruction's throughput
                has elapsed, even if this instruction latency hasn't elapsed yet.
            latency (int): Number of clock cycles it takes for the instruction to complete and its outputs to be ready.
                Outputs are ready in the clock cycle after this instruction's latency has elapsed. Must be
                greater than or equal to throughput.
            comment (str): Optional comment for the instruction.

        Raises:
            ValueError: If throughput is less than 1 or latency is less than throughput.
        """
        # validate inputs
        if throughput < 1:
            raise ValueError(("`throughput`: must be a positive number, "
                              "but {} received.".format(throughput)))
        if latency < throughput:
            raise ValueError(("`latency`: cannot be less than throughput. "
                              "Expected, at least, {}, but {} received.".format(throughput, latency)))

        super().__init__((0, 0))

        self.__id = (id, next(BaseInstruction.__id_count)) # Mix with unique sequence counter
        self.__throughput = throughput # read_only throughput of the operation
        self.__latency = latency # read_only latency of the operation
        self._dests = []
        self._sources = []
        self.comment = " id: {}{}{}".format(self.__id,
                                            "; " if comment.strip() else "",
                                            comment)
        self.__schedule_timing: ScheduleTiming = None # Tracks when was this instruction scheduled, or None if not scheduled yet

        self._frozen_pisa = "" # To contain frozen P-ISA format after scheduling
        self._frozen_xisa = "" # To contain frozen XInst in ASM ISA format after scheduling
        self._frozen_cisa = "" # To contain frozen CInst in ASM ISA format after scheduling
        self._frozen_misa = "" # To contain frozen MInst in ASM ISA format after scheduling

    def __repr__(self):
        """
        Returns a string representation of the BaseInstruction object.
        """
        retval = ('<{}({}) object at {}>(id={}[0], '
                  'dst={}, src={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.OP_NAME_PISA,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.dests,
                                                           self.sources,
                                                           self.throughput,
                                                           self.latency)
        return retval

    def __eq__(self, other):
        """
        Checks equality between two BaseInstruction objects.
        """
        return self is other #other.id == self.id

    def __hash__(self):
        """
        Returns the hash of the BaseInstruction object.
        """
        return hash(self.id)

    def __str__(self):
        """
        Returns a string representation of the BaseInstruction object.
        """
        return f'{self.name} {self.id}'

    # Methods and properties
    # ----------------------------

    @property
    def id(self) -> tuple:
        """
        Gets the unique ID for the instruction.

        This is a combination of the client ID specified during construction and a unique nonce per instruction.

        Returns:
            tuple: (client_id: int, nonce: int) where client_id is the id specified at construction.
        """
        return self.__id

    @property
    def schedule_timing(self) -> ScheduleTiming:
        """
        Retrieves the 1-based index for this instruction in its schedule listing,
        or less than 1 if not scheduled yet.
        """
        return self.__schedule_timing

    def set_schedule_timing_index(self, value: int):
        """
        Sets the schedule timing index.

        Parameters:
            value (int): The index value to set.

        Raises:
            ValueError: If the value is less than 0.
        """
        if value < 0:
            raise ValueError("`value`: expected a value of `0` or greater for `schedule_timing.index`.")
        self.__schedule_timing = ScheduleTiming(cycle = self.__schedule_timing.cycle,
                                                index=value)

    @property
    def is_scheduled(self) -> bool:
        """
        Checks if the instruction is scheduled.

        Returns:
            bool: True if the instruction is scheduled, False otherwise.
        """
        return True if self.schedule_timing else False

    @property
    def throughput(self) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput.
        """
        return self.__throughput

    @property
    def latency(self) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency.
        """
        return self.__latency

    @property
    def dests(self) -> list:
        """
        Gets the list of destination objects.

        Returns:
            list: The list of destination objects.
        """
        return self._dests

    @dests.setter
    def dests(self, value):
        """
        Sets the list of destination objects.

        Parameters:
            value (list): The list of destination objects to set.
        """
        self._set_dests(value)

    def _set_dests(self, value):
        """
        Validates and sets the list of destination objects.

        Parameters:
            value (list): The list of destination objects to set.

        Raises:
            ValueError: If the value is not a list of CycleTracker objects.
        """
        if not all(isinstance(x, CycleTracker) for x in value):
            raise ValueError("`value`: Expected list of `CycleTracker` objects.")
        self._dests = [ x for x in value ]

    @property
    def sources(self) -> list:
        """
        Gets the list of source objects.

        Returns:
            list: The list of source objects.
        """
        return self._sources

    @sources.setter
    def sources(self, value):
        """
        Sets the list of source objects.

        Parameters:
            value (list): The list of source objects to set.
        """
        self._set_sources(value)

    def _set_sources(self, value):
        """
        Validates and sets the list of source objects.

        Parameters:
            value (list): The list of source objects to set.

        Raises:
            ValueError: If the value is not a list of CycleTracker objects.
        """
        if not all(isinstance(x, CycleTracker) for x in value):
            raise ValueError("`value`: Expected list of `CycleTracker` objects.")
        self._sources = [ x for x in value ]

    def _get_cycle_ready(self):
        """
        Returns the current value for ready cycle.

        This method is called by property cycle_ready getter to retrieve the value.
        An instruction cycle ready value is the maximum among its own and all the
        sources ready cycles, and destinations (special case).

        Cycles are measured as tuples: (bundle: int, clock_cycle: int)

        Overrides `CycleTracker._get_cycle_ready`.

        Returns:
            CycleType: The current value for ready cycle.
        """

        # we have to be careful that `max` won't iterate on our CycleType tuples' inner values
        retval = super()._get_cycle_ready()
        if self.sources:
            retval = max(retval, *(src.cycle_ready for src in self.sources))
        if self.dests:
            # dests cycle ready is a special case:
            # dests are ready to be read or writen to at their cycle_ready, but instructions can
            # start the following cycle when their dests are ready minus the latency of
            # the instruction because the dests will be writen to in the last cycle of
            # the instruction:
            # Cycle decode_phase    write_phase dests_ready latency
            #     1 INST1                                   5
            #     2 INST2                                   5
            #     3 INST3                                   5
            #     4 INST4                                   5
            #     5 INST6           INST1                   5
            #     6 INST7           INST2       INST1       5
            #     7 INST8           INST3       INST2       5
            # INST1's dests are ready in cycle 6 and they are writen to in cycle 5.
            # If INST2 uses any INST1 dest as its dest, INST2 can start the cycle
            # following INST1, 2, because INST2 will write to the same dest in cycle 6.
            retval = max(retval, *(dst.cycle_ready - self.latency + 1 for dst in self.dests))
        return retval

    def freeze(self):
        """
        Called immediately after `_schedule()` to freeze the instruction after scheduling
        to preserve the instruction string representation to output into the listing.
        Changes made to the instruction and its components after freezing are ignored.

        Freezing is necessary because content of instruction sources and destinations
        may change by further instructions as they get scheduled.

        Clients may call this method stand alone if they need to refresh the frozen
        instruction. However, refreezing may result in incorrect string representation
        depending on the instruction.

        This method ensures that the instruction can be frozen.

        Derived classes should override to correctly freeze the instruction.
        When overriding, this base method must be called as part of the override.

        Raises:
            RuntimeError: If the instruction has not been scheduled yet.
        """
        if not self.is_scheduled:
            raise RuntimeError(f"Instruction `{self.name}` (id = {self.id}) is not yet scheduled.")

        self._frozen_pisa = self._toPISAFormat()
        self._frozen_xisa = self._toXASMISAFormat()
        self._frozen_cisa = self._toCASMISAFormat()
        self._frozen_misa = self._toMASMISAFormat()

    def _schedule(self, cycle_count: CycleType, schedule_idx: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Ensures that this instruction is ready to be scheduled (dependencies and states
        are ready).

        Derived classes can override to add their own simulation rules. When overriding,
        this base method must be called, at some point, as part of the override.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_idx (int): 1-based index for this instruction in its schedule listing.

        Raises:
            ValueError: If invalid arguments are provided.
            RuntimeError: If the instruction is not ready to be scheduled yet or if the instruction is already scheduled.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
            the current cycle counter.
        """
        if self.is_scheduled:
            raise RuntimeError(f"Instruction `{self.name}` (id = {self.id}) is already scheduled.")
        if schedule_idx < 1:
            raise ValueError("`schedule_idx`: expected a value of `1` or greater.")
        if len(cycle_count) < 2:
            raise ValueError("`cycle_count`: expected a pair/tuple with two components.")
        if cycle_count < self.cycle_ready:
            raise RuntimeError(("Instruction {}, id: {}, not ready to schedule. "
                                "Ready cycle is {}, but current cycle is {}.").format(self.name,
                                                                                      self.id,
                                                                                      self.cycle_ready,
                                                                                      cycle_count))
        self.__schedule_timing = ScheduleTiming(cycle_count, schedule_idx)
        return self.throughput

    @final
    def schedule(self, cycle_count: CycleType, schedule_idx: int) -> int:
        """
        Schedules and freezes the instruction, simulating timings of executing this instruction.

        Ensures that this instruction is ready to be scheduled (dependencies and states
        are ready).

        Derived classes can override the protected methods `_schedule()` and `_freeze()` to add their
        own simulation and freezing rules.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_idx (int): 1-based index for this instruction in its schedule listing.

        Raises:
            ValueError: If invalid arguments are provided.
            RuntimeError: If the instruction is not ready to be scheduled yet or if the instruction is already scheduled.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
            the current cycle counter.
        """
        retval = self._schedule(cycle_count, schedule_idx)
        self.freeze()
        return retval

    def toStringFormat(self,
                       preamble,
                       op_name: str,
                       *extra_args) -> str:
        """
        Converts the instruction to a string format.

        Parameters:
            preamble (iterable): List of arguments prefacing the instruction name `op_name`. Can be None if no preamble.
            op_name (str): Name of the operation for the instruction. Cannot be empty.
            extra_args: Variable number of arguments. Extra arguments to add at the end of the instruction.

        Returns:
            str: A string representing the instruction. The string has the form:
            [preamble0, preamble1, ..., preamble_p,] op [, extra0, extra1, ..., extra_e] [# comment]
        """
        # op, dst0 (bank), dst1 (bank), ..., dst_d (bank), src0 (bank), src1 (bank), ..., src_s (bank) [, extra], res # comment
        if not op_name:
            raise ValueError("`op_name` cannot be empty.")
        retval = op_name
        if preamble:
            retval = ('{}, '.format(', '.join(str(x) for x in preamble))) + retval
        if extra_args:
            retval += ', {}'.format(', '.join([str(extra) for extra in extra_args]))
        if not GlobalConfig.suppressComments:
            if self.comment:
                retval += ' #{}'.format(self.comment)
        return retval

    @final
    def toPISAFormat(self) -> str:
        """
        Converts the instruction to P-ISA kernel format.

        Returns:
            str: String representation of the instruction in P-ISA kernel format. The string has the form:
            `N, op, dst0 (bank), dst1 (bank), ..., dst_d (bank), src0 (bank), src1 (bank), ..., src_s (bank) [, extra0, extra1, ..., extra_e] [, res] [# comment]`
            where `extra_e` are instruction specific extra arguments.
        """
        return self._frozen_pisa if self._frozen_pisa else self._toPISAFormat()

    @final
    def toXASMISAFormat(self) -> str:
        """
        Converts the instruction to ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `_toXASMISAFormat()`.

        Derived classes can override method `_toXASMISAFormat()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `id[0], N, op, dst_register0, dst_register1, ..., dst_register_d, src_register0, src_register1, ..., src_register_s [, extra0, extra1, ..., extra_e], res [# comment]`
            where `extra_e` are instruction specific extra arguments.
            Since the residual is mandatory in the format, it is set to `0` in the output if the
            instruction does not support residual.
        """
        return self._frozen_xisa if self._frozen_xisa else self._toXASMISAFormat()

    @final
    def toCASMISAFormat(self) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `_toCASMISAFormat()`.

        Derived classes can override method `_toCASMISAFormat()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `N, op, dst0, dst1, ..., dst_d, src0, src1, ..., src_s [, extra0, extra1, ..., extra_e], [# comment]`
            where `extra_e` are instruction specific extra arguments.
            Since the ring size is mandatory in the format, it is set to `0` in the output if the
            instruction does not support it.
        """
        return self._frozen_cisa if self._frozen_cisa else self._toCASMISAFormat()

    @final
    def toMASMISAFormat(self) -> str:
        """
        Converts the instruction to MInst ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `_toMASMISAFormat()`.

        Derived classes can override method `_toMASMISAFormat()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `op, dst0, dst1, ..., dst_d, src0, src1, ..., src_s [, extra0, extra1, ..., extra_e], [# comment]`
            where `extra_e` are instruction specific extra arguments.
        """
        return self._frozen_misa if self._frozen_misa else self._toMASMISAFormat()

    def _toPISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to P-ISA kernel format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have a P-ISA equivalent.
        """
        return ""

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to XInst ASM-ISA format.

        This base method returns an empty string.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have an XInst equivalent.
        """
        return ""

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have a CInst equivalent.
        """
        return ""

    def _toMASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to MInst ASM-ISA format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have an MInst equivalent.
        """
        return ""
