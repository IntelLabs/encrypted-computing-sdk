
from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model.variable import Variable

class Instruction(CInstruction):
    """
    Encapsulates an `nload` CInstruction.

    `nload` instruction loads metadata (for NTT/iNTT routing mapping) from scratchpad
    into special routing table registers.

    For more information, check the `nload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nload.md

    Attributes:
        table_idx (int): Index for destination routing table. See docs.
        spad_src (int): SPAD address of metadata variable to load.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'nload'.
        """
        return "nload"

    def __init__(self,
                 id: int,
                 table_idx: int,
                 src: Variable,
                 mem_model,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `nload` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            table_idx (int): Index for destination routing table. See docs.

            src (Variable): Variable containing the metadata to load from SPAD.

            mem_model: The memory model used for tracking SPAD access.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `mem_model` is `None`.
        """
        if not mem_model:
            raise ValueError('`mem_model` cannot be `None`.')
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.table_idx = table_idx
        self.__mem_model = mem_model
        self._set_sources([src])

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, table index, source, throughput, and latency.
        """
        assert(len(self.sources) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'table_idx={}, src={}, '
                  'mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.table_idx,
                                                           self.sources[0],
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Raises an error as the instruction does not have destination parameters.

        Parameters:
            value: The value to set as destination, which is not applicable.

        Raises:
            RuntimeError: Always raised as the instruction does not have destination parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _set_sources(self, value):
        """
        Sets the source variables for the instruction.

        Parameters:
            value (list): A list of `Variable` objects to set as sources.

        Raises:
            ValueError: If the number of sources is incorrect.
            TypeError: If the list does not contain `Variable` objects.
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

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: If the variable is not allocated in SPAD or if the table index is invalid.
                See inherited for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable: Variable = self.sources[0] # Expected sources to contain a Variable
        if variable.spad_address < 0:
            raise RuntimeError(f"Null Access Violation: Variable `{variable}` not allocated in SPAD.")
        if self.table_idx < 0:
            raise RuntimeError("Invalid `table_idx` negative routing table index.")

        retval = super()._schedule(cycle_count, schedule_id)
        # Track last access to SPAD address
        spad_access_tracking = self.__mem_model.spad.getAccessTracking(variable.spad_address)
        spad_access_tracking.last_cload = self
        # No need to sync to any previous MLoads after bones
        spad_access_tracking.last_mload = None
        return retval

    def _toCASMISAFormat(self, *extra_args) -> str:
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

        # `op, target_idx, spad_src [# comment]`
        preamble = []
        # Instruction sources
        extra_args = tuple(src.toCASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        extra_args = (self.table_idx, ) + extra_args
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)