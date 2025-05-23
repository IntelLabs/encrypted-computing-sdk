from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model.variable import Variable

class Instruction(CInstruction):
    """
    Encapsulates the `bload` CInstruction.

    The `bload` instruction loads metadata from the scratchpad to special registers in the register file.
    
    For more information, check the `bload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bload.md

    Attributes:
        col_num (int): Block index inside the metadata source word. See documentation for details.
        m_idx (int): Target metadata register index. See documentation for details.
        spad_src (int): SPAD address of the metadata word to load.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name for the operation.

        Returns:
            str: The ASM name for the operation, which is "bload".
        """
        return "bload"

    def __init__(self,
                 id: int,
                 col_num: int,
                 m_idx: int,
                 src: Variable,
                 mem_model,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Constructs a new `bload` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            col_num (int): Metadata register column number. See documentation for details.
            m_idx (int): Metadata register index. See documentation for details.
            src (Variable): Metadata variable to load from SPAD.
            mem_model: The memory model associated with the instruction.
            throughput (int, optional): The throughput of the instruction. Defaults to the class-defined throughput.
            latency (int, optional): The latency of the instruction. Defaults to the class-defined latency.
            comment (str, optional): An optional comment for the instruction.

        Raises:
            ValueError: If `mem_model` is None.
        """
        if not mem_model:
            raise ValueError('`mem_model` cannot be `None`.')
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.col_num = col_num
        self.m_idx = m_idx
        self.__mem_model = mem_model
        self._set_sources( [ src ] )

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation.
        """
        assert(len(self.sources) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'col_num={}, m_idx={}, src={}, '
                  'mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.col_num,
                                                           self.m_idx,
                                                           self.sources[0],
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Raises an error as the `bload` instruction does not have destination parameters.

        Parameters:
            value: The value to set as destinations.

        Raises:
            RuntimeError: Always, as `bload` does not have destination parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have destination parameters.")

    def _set_sources(self, value):
        """
        Validates and sets the list of source objects.

        Parameters:
            value (list): The list of source objects to set.

        Raises:
            ValueError: If the value is not a list of the expected number of `Variable` objects.
        """
        if len(value) != Instruction._OP_NUM_SOURCES:
            raise ValueError(("`value`: Expected list of {} `Variable` objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_SOURCES,
                                                                           len(value))))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of `Variable` objects.")
        super()._set_sources(value)

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_id (int): The schedule ID for the instruction.

        Raises:
            RuntimeError: If the SPAD address is invalid or if the column number is out of range.

        Returns:
            int: The throughput for this instruction, i.e., the number of cycles by which to advance
            the current cycle counter.
        """
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable: Variable = self.sources[0] # expected sources to contain a Variable
        if variable.spad_address < 0:
            raise RuntimeError(f'Null Access Violation: Variable "{variable}" not allocated in SPAD.')
        if self.m_idx < 0:
            raise RuntimeError(f"Invalid negative index `m_idx`.")
        if self.col_num not in range(4):
            raise RuntimeError(f"Invalid `col_num`: {self.col_num}. Must be in range [0, 4).")

        retval = super()._schedule(cycle_count, schedule_id)
        # Track last access to SPAD address
        spad_access_tracking = self.__mem_model.spad.getAccessTracking(variable.spad_address)
        spad_access_tracking.last_cload = self
        # No need to sync to any previous MLoads after bload
        spad_access_tracking.last_mload = None
        return retval

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            extra_args: Additional arguments for the conversion.

        Raises:
            ValueError: If `extra_args` are provided.

        Returns:
            str: The ASM format string of the instruction.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # `op, target_idx, spad_src [# comment]`
        preamble = []
        # Instruction sources
        extra_args = (self.col_num, )
        extra_args = tuple(src.toCASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        extra_args = (self.m_idx, ) + extra_args
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)
