# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""BaseInstruction and related classes for assembler instructions."""
from typing import final, NamedTuple, List, Optional

# pylint: disable=too-many-instance-attributes, too-many-public-methods

from assembler.common.config import GlobalConfig
from assembler.common.counter import Counter
from assembler.common.cycle_tracking import CycleTracker, CycleType
from assembler.common.decorators import classproperty


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
        op_name_asm (str): ASM-ISA name for the instruction.
        op_name_pisa (str): P-ISA name for the instruction.

    Class Methods:
        _get_name(self) -> str: Derived classes should implement this method and return the correct
            name for the instruction. Defaults to the ASM-ISA name.
        _get_op_name_asm(self) -> str: Derived classes should implement this method and return the correct
            ASM name for the operation. Default throws not implemented.
        _get_op_name_pisa(self) -> str: Derived classes should implement this method and return the correct
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
        _to_casmisa_format(self, *extra_args) -> str: Converts the instruction to CInst ASM-ISA format.
            Derived classes should override with their functionality.
        _to_masmisa_format(self, *extra_args) -> str: Converts the instruction to MInst ASM-ISA format.
            Derived classes should override with their functionality.
        _to_pisa_format(self, *extra_args) -> str: Converts the instruction to P-ISA kernel format.
            Derived classes should override with their functionality.
        _to_xasmisa_format(self, *extra_args) -> str: Converts the instruction to XInst ASM-ISA format.
            Derived classes should override with their functionality.
        freeze(self): Called immediately after _schedule() to freeze the instruction after scheduling
            to preserve the instruction string representation to output into the listing.
            Changes made to the instruction and its components after freezing are ignored.
        schedule(self, cycle_count: CycleType, schedule_idx: int) -> int:
            Schedules and freezes the instruction, simulating timings of executing this instruction.
        to_string_format(self, preamble, op_name: str, *extra_args) -> str:
            Converts the instruction to a string format.
        to_pisa_format(self) -> str: Converts the instruction to P-ISA kernel format.
        to_xasmisa_format(self) -> str: Converts the instruction to ASM-ISA format.
        to_casmisa_format(self) -> str: Converts the instruction to CInst ASM-ISA format.
        to_masmisa_format(self) -> str: Converts the instruction to MInst ASM-ISA format.
    """

    # To be initialized from ASM ISA spec
    _OP_NUM_DESTS: int
    _OP_NUM_SOURCES: int
    _OP_DEFAULT_THROUGHPUT: int
    _OP_DEFAULT_LATENCY: int

    __id_count = Counter.count(
        0
    )  # internal unique sequence counter to generate unique IDs

    # Class methods and properties
    # ----------------------------
    @classmethod
    def isa_spec_as_dict(cls) -> dict:
        """Returns attributes as dictionary."""
        spec = {
            "num_dests": cls._OP_NUM_DESTS,
            "num_sources": cls._OP_NUM_SOURCES,
            "default_throughput": cls._OP_DEFAULT_THROUGHPUT,
            "default_latency": cls._OP_DEFAULT_LATENCY,
        }
        return spec

    @classmethod
    def set_num_dests(cls, val):
        """Set the number of destination operands."""
        cls._OP_NUM_DESTS = val

    @classmethod
    def set_num_sources(cls, val):
        """Set the number of source operands."""
        cls._OP_NUM_SOURCES = val

    @classmethod
    def set_default_throughput(cls, val):
        """Set the default throughput."""
        cls._OP_DEFAULT_THROUGHPUT = val

    @classmethod
    def set_default_latency(cls, val):
        """Set the default latency."""
        cls._OP_DEFAULT_LATENCY = val

    @classproperty
    def name(self) -> str:
        """Name for the instruction."""
        return self._get_name()

    @classmethod
    def _get_name(cls) -> str:
        """Derived classes should implement this method and return correct name for the instruction."""
        return cls.op_name_asm

    @classproperty
    def op_name_pisa(self) -> str:
        """P-ISA name for the instruction."""
        return self._get_op_name_pisa()

    @classmethod
    def _get_op_name_pisa(cls) -> str:
        """Derived classes should implement this method and return correct P-ISA name for the operation."""
        return cls.op_name_asm

    @classproperty
    def op_name_asm(self) -> str:
        """ASM-ISA name for instruction."""
        return self._get_op_name_asm()

    @classmethod
    def _get_op_name_asm(cls) -> str:
        """Derived classes should implement this method and return correct ASM name for the operation."""
        raise NotImplementedError("Abstract method not implemented.")

    # Constructor
    # -----------

    def __init__(
        self, instruction_id: int, throughput: int, latency: int, comment: str = ""
    ):
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
            raise ValueError(
                (
                    f"`throughput`: must be a positive number, "
                    f"but {throughput} received."
                )
            )
        if latency < throughput:
            raise ValueError(
                (
                    f"`latency`: cannot be less than throughput. "
                    f"Expected, at least, {throughput}, but {latency} received."
                )
            )

        super().__init__(CycleType(0, 0))
        self.__id = (instruction_id, next(BaseInstruction.__id_count))
        self.__throughput = throughput
        self.__latency = latency
        self._dests: List[CycleTracker] = []
        self._sources: List[CycleTracker] = []
        self.comment = f" id: {self.__id}{'; ' if comment.strip() else ''}{comment}"
        self.__schedule_timing: Optional[ScheduleTiming] = None
        self._frozen_pisa = ""
        self._frozen_xisa = ""
        self._frozen_cisa = ""
        self._frozen_misa = ""

    def __repr__(self):
        """Returns a string representation of the BaseInstruction object."""
        retval = (
            f"<{type(self).__name__}({self.op_name_pisa}) object at {hex(id(self))}>(id={self.id}[0], "
            f"dst={self.dests}, src={self.sources}, "
            f"throughput={self.throughput}, latency={self.latency})"
        )
        return retval

    def __eq__(self, other):
        """Checks equality between two BaseInstruction objects."""
        return self is other

    def __hash__(self):
        """Returns the hash of the BaseInstruction object."""
        return hash(self.id)

    def __str__(self):
        """Returns a string representation of the BaseInstruction object."""
        return f"{self.name} {self.id}"

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
            raise ValueError(
                "`value`: expected a value of `0` or greater for `schedule_timing.index`."
            )
        self.__schedule_timing = ScheduleTiming(
            cycle=self.__schedule_timing.cycle, index=value
        )

    @property
    def is_scheduled(self) -> bool:
        """
        Checks if the instruction is scheduled.

        Returns:
            bool: True if the instruction is scheduled, False otherwise.
        """
        return bool(self.schedule_timing)

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
        self._dests = list(value)

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
        self._sources = list(value)

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
            # dests are ready to be read or written to at their cycle_ready, but instructions can
            # start the following cycle when their dests are ready minus the latency of
            # the instruction because the dests will be written to in the last cycle of
            # the instruction:
            # Cycle decode_phase    write_phase dests_ready latency
            #     1 INST1                                   5
            #     2 INST2                                   5
            #     3 INST3                                   5
            #     4 INST4                                   5
            #     5 INST6           INST1                   5
            #     6 INST7           INST2       INST1       5
            #     7 INST8           INST3       INST2       5
            # INST1's dests are ready in cycle 6 and they are written to in cycle 5.
            # If INST2 uses any INST1 dest as its dest, INST2 can start the cycle
            # following INST1, 2, because INST2 will write to the same dest in cycle 6.
            retval = max(
                retval, *(dst.cycle_ready - self.latency + 1 for dst in self.dests)
            )
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
            raise RuntimeError(
                f"Instruction `{self.name}` (id = {self.id}) is not yet scheduled."
            )

        self._frozen_pisa = self._to_pisa_format()
        self._frozen_xisa = self._to_xasmisa_format()
        self._frozen_cisa = self._to_casmisa_format()
        self._frozen_misa = self._to_masmisa_format()

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
            raise RuntimeError(
                f"Instruction `{self.name}` (id = {self.id}) is already scheduled."
            )
        if schedule_idx < 1:
            raise ValueError("`schedule_idx`: expected a value of `1` or greater.")
        if len(cycle_count) < 2:
            raise ValueError(
                "`cycle_count`: expected a pair/tuple with two components."
            )
        if cycle_count < self.cycle_ready:
            raise RuntimeError(
                f"Instruction {self.name}, id: {self.id}, not ready to schedule. "
                f"Ready cycle is {self.cycle_ready}, but current cycle is {cycle_count}."
            )
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

    def to_string_format(self, preamble, op_name: str, *extra_args) -> str:
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
            retval = f'{", ".join(str(x) for x in preamble)}, {retval}'
        if extra_args:
            retval += f', {", ".join([str(extra) for extra in extra_args])}'
        if not GlobalConfig.suppressComments:
            if self.comment:
                retval += f" #{self.comment}"
        return retval

    @final
    def to_pisa_format(self) -> str:
        """
        Converts the instruction to P-ISA kernel format.

        Returns:
            str: String representation of the instruction in P-ISA kernel format. The string has the form:
            `N, op, dst0 (bank), dst1 (bank), ..., dst_d (bank), src0 (bank), src1 (bank), ..., src_s (bank) [, extra0, extra1, ..., extra_e] [, res] [# comment]`
            where `extra_e` are instruction specific extra arguments.
        """
        return self._frozen_pisa if self._frozen_pisa else self._to_pisa_format()

    @final
    def to_xasmisa_format(self) -> str:
        """
        Converts the instruction to ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `_to_xasmisa_format()`.

        Derived classes can override method `_to_xasmisa_format()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `id[0], N, op, dst_register0, dst_register1, ..., dst_register_d, src_register0, src_register1, ..., src_register_s [, extra0, extra1, ..., extra_e], res [# comment]`
            where `extra_e` are instruction specific extra arguments.
            Since the residual is mandatory in the format, it is set to `0` in the output if the
            instruction does not support residual.
        """
        return self._frozen_xisa if self._frozen_xisa else self._to_xasmisa_format()

    @final
    def to_casmisa_format(self) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `__to_casmisa_format()`.

        Derived classes can override method `__to_casmisa_format()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `N, op, dst0, dst1, ..., dst_d, src0, src1, ..., src_s [, extra0, extra1, ..., extra_e], [# comment]`
            where `extra_e` are instruction specific extra arguments.
            Since the ring size is mandatory in the format, it is set to `0` in the output if the
            instruction does not support it.
        """
        return self._frozen_cisa if self._frozen_cisa else self._to_casmisa_format()

    @final
    def to_masmisa_format(self) -> str:
        """
        Converts the instruction to MInst ASM-ISA format.

        If instruction is frozen, this returns the frozen result, otherwise, it attempts to
        generate the string representation on the fly.

        Internally calls method `_to_masmisa_format()`.

        Derived classes can override method `_to_masmisa_format()` to provide their own conversion.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
            `op, dst0, dst1, ..., dst_d, src0, src1, ..., src_s [, extra0, extra1, ..., extra_e], [# comment]`
            where `extra_e` are instruction specific extra arguments.
        """
        return self._frozen_misa if self._frozen_misa else self._to_masmisa_format()

    def _to_pisa_format(self, *extra_args) -> str:  # pylint: disable=unused-argument
        """
        Converts the instruction to P-ISA kernel format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have a P-ISA equivalent.
        """
        return ""

    def _to_xasmisa_format(self, *extra_args) -> str:  # pylint: disable=unused-argument
        """
        Converts the instruction to XInst ASM-ISA format.

        This base method returns an empty string.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have an XInst equivalent.
        """
        return ""

    def _to_casmisa_format(self, *extra_args) -> str:  # pylint: disable=unused-argument
        """
        Converts the instruction to CInst ASM-ISA format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have a CInst equivalent.
        """
        return ""

    def _to_masmisa_format(self, *extra_args) -> str:  # pylint: disable=unused-argument
        """
        Converts the instruction to MInst ASM-ISA format.

        Derived classes should override with their functionality. Overrides do not need to call
        this base method.

        Returns:
            str: Empty string ("") to indicate that this instruction does not have an MInst equivalent.
        """
        return ""
