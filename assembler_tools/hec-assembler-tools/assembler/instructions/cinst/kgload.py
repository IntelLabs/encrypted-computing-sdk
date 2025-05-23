from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model.variable import Variable
from assembler.memory_model.register_file import Register

class Instruction(CInstruction):
    """
    Encapsulates `kg_load` CInstruction.

    `kg_load` instruction loads HW-generated key material from the keygen engine
    into a CE data register.

    To start the keygen engine, a seed should be loaded followed by a kg_start
    instruction to start the key material generation.

    kg_load, dst_register

    Rules:
    1. `kg_load`s and `kg_start`s must be `latency` cycles apart from any other
    `kg_load` and `kg_start`. It takes between 10 to `latency` cycles for the key generation
    resource to generate the next key material, possibly causing contention if
    the key material is requested by any `kg_load` within `latency` cycles.
    """

    @classmethod
    def SetNumSources(cls, val):
        cls._OP_NUM_SOURCES = val + 1 # Adding the keygen variable (since the actual instruction needs no sources)

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'kg_load'.
        """
        return "kg_load"

    def __init__(self,
                 id: int,
                 dst: Register,
                 src: list,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `kg_load` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            dst (Register): Register to contain the key material generated. Associated keygen variable will
                            be set to this register when scheduled.

            src (list of Variable): Contains the keygen variable to be loaded. The variable register will be set
                                    to the specified destination register when scheduled.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self._set_sources(src)
        self._set_dests([dst])

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, column number, memory index, source, throughput, and latency.
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
        Sets the destination registers for the instruction.

        Parameters:
            value (list): A list of `Register` objects to set as destinations.

        Raises:
            ValueError: If the number of destinations is incorrect.
            TypeError: If the list does not contain `Register` objects.
        """
        if len(value) != Instruction._OP_NUM_DESTS:
            raise ValueError(("`value`: Expected list of {} `Register` objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_DESTS,
                                                                           len(value))))
        if not all(isinstance(x, Register) for x in value):
            raise TypeError("`value`: Expected list of `Register` objects.")
        super()._set_dests(value)

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

        Source Variable and destination Register will be updated to reflect the load.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: Variable or Register already allocated. See inherited for other exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        assert(Instruction._OP_NUM_DESTS > 0 and len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable: Variable = self.sources[0] # Expected sources to contain a Variable
        target_register: Register = self.dests[0]

        if variable.spad_address >= 0 or variable.hbm_address >= 0:
            raise RuntimeError(f"Variable `{variable}` already generated.")
        # Cannot allocate variable to more than one register (memory coherence)
        # and must not overwrite a register that already contains a variable.
        if variable.register:
            raise RuntimeError(f"Variable `{variable}` already allocated in register `{variable.register}`.")
        if target_register.contained_variable:
            raise RuntimeError(f"Register `{target_register}` already contains a Variable object.")

        retval = super()._schedule(cycle_count, schedule_id)
        # Variable generated, reflect the load
        target_register.allocateVariable(variable)

        if self.comment:
            self.comment += ';'
        self.comment += f' {variable.name}'

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

        # `op, dest_reg [# comment]`
        preamble = []
        # Instruction sources
        # kg_load has no sources

        # Instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)