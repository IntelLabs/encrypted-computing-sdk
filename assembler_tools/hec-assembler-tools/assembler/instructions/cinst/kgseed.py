from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model.variable import Variable

class Instruction(CInstruction):
    """
    Encapsulates `kg_seed` CInstruction.

    `kg_seed` instruction loads a seed value into the keygen engine. The engine
    is reset and prepared to start generating key material.

    A word holds up to 4 seed values (2KB each), so, kg_seed has extra parameters
    to select the seed inside the word.

    kg_seed, <spad_address>, <block_index>

    spad_address: SPAD address where the word containing the seed resides.
    block_index: Index of data block inside the word for the seed to load.
        A word is 8KB, containing up to 4 seeds of 2KB each. `block_index`
        indicates the index of the block to load.

    Attributes:
        block_index (int): Index of data block inside the word for the seed to load.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'kg_seed'.
        """
        return "kg_seed"

    def __init__(self,
                 id: int,
                 block_index: int,
                 src: Variable,
                 mem_model,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `kg_seed` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            block_index (int): Index of data block inside the word for the seed to load. See docs.

            src (Variable): Variable containing the seed to load from SPAD.

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
        self.block_index = block_index
        self.__mem_model = mem_model
        self._set_sources([src])

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, block index, source, throughput, and latency.
        """
        assert(len(self.sources) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'col_num={}, m_idx={}, src={}, '
                  'mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.block_index,
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
        raise RuntimeError(f"Instruction `{self.name}` does not have destination parameters.")

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
            RuntimeError: If the variable is not allocated in SPAD or if the block index is invalid.
                See inherited for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable: Variable = self.sources[0] # Expected sources to contain a Variable
        if variable.spad_address < 0:
            raise RuntimeError(f'Null Access Violation: Variable "{variable}" not allocated in SPAD.')
        if self.block_index not in range(4):
            raise RuntimeError(f"Invalid `block_index`: {self.block_index}. Must be in range [0, 4).")

        retval = super()._schedule(cycle_count, schedule_id)
        # Track last access to SPAD address
        spad_access_tracking = self.__mem_model.spad.getAccessTracking(variable.spad_address)
        spad_access_tracking.last_cload = self
        # No need to sync to any previous MLoads after kg_seed
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

        # `op, spad_src, block_index [# comment]`
        preamble = []
        # Instruction sources
        extra_args = (self.block_index, )
        extra_args = tuple(src.toCASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)