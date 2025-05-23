from assembler.common.cycle_tracking import CycleType
from .xinstruction import XInstruction
from assembler.memory_model.variable import Variable, DummyVariable
from assembler.memory_model.register_file import Register

class Instruction(XInstruction):
    """
    Encapsulates a `move` instruction used to copy data from one register to a different one.

    This class is responsible for managing the movement of variables between registers
    in accordance with a specific instruction set architecture (ISA) specification.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_move.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: The operation name as a string.
        """
        return "move"

    def __init__(self,
                 id: int,
                 dst: Register,
                 src: list,
                 dummy_var: DummyVariable = None,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `move` CInstruction.

        Parameters:
            id (int): 
                User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            dst (Register): 
                The destination register where to load the variable in `src`.
            src (list of Variable): 
                A list containing a single Variable object indicating the source variable to move from
                its current register to `dst` register.
            dummy_var (DummyVariable, optional): 
                A dummy variable used for marking registers as free.
            throughput (int, optional): 
                The throughput of the instruction. Defaults to the class-level default if not provided.
            latency (int, optional): 
                The latency of the instruction. Defaults to the class-level default if not provided.
            comment (str, optional): 
                An optional comment for the instruction.

        Raises:
            ValueError: If a dummy variable is used as a source or if the destination register is not empty.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        if any(isinstance(v, DummyVariable) or not v.name for v in src):
            raise ValueError(f"{Instruction.OP_NAME_ASM} cannot have dummy variable as source.")
        if dst.contained_variable \
           and not isinstance(dst.contained_variable, DummyVariable):
            raise ValueError("{}: destination register must be empty, but variable {}.{} found.".format(Instruction.OP_NAME_ASM,
                                                                                                        dst.contained_variable.name,
                                                                                                        dst.contained_variable.tag))
        N = 0  # Does not require ring-size
        super().__init__(id, N, throughput, latency, comment=comment)
        self.__dummy_var = dummy_var
        self._set_dests([dst])
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the object.
        """
        retval = ('<{}({}) object at {}>(id={}[0], '
                  'dst={}, src={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                       self.name,
                                                       hex(id(self)),
                                                       self.id,
                                                       self.dests,
                                                       self.sources,
                                                       self.throughput,
                                                       self.latency)
        return retval

    def _set_dests(self, value):
        """
        Sets the destination register for the instruction.

        Parameters:
            value (list): A list of Register objects representing the destination.

        Raises:
            ValueError: If the list does not contain the expected number of Register objects.
            TypeError: If the list contains non-Register objects.
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
        Sets the source variable for the instruction.

        Parameters:
            value (list): A list of Variable objects representing the source.

        Raises:
            ValueError: If the list does not contain the expected number of Variable objects.
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

        Scheduling `move` XInst will cause the involved registers and variables to be
        updated. The source register for the variable will be freed, and the variable
        will be allocated to the destination register.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_id (int): The schedule identifier.

        Raises:
            RuntimeError: If the instruction is not ready to execute yet or if the target register is not empty.

        Returns:
            int: The throughput for this instruction, i.e., the number of cycles by which to advance
                the current cycle counter.
        """
        assert(Instruction._OP_NUM_DESTS > 0 and len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable = self.sources[0]  # Expected sources to contain a Variable
        target_register = self.dests[0]
        if isinstance(variable, Register):
            # Source and target types are swapped after scheduling
            # Instruction already scheduled: can only schedule once
            assert(isinstance(target_register, Variable))
            raise RuntimeError(f'Instruction `{self.name}` (id = {self.id}) already scheduled.')

        if target_register.contained_variable \
            and not isinstance(target_register.contained_variable, DummyVariable):
            raise RuntimeError(('Instruction `{}` (id = {}) '
                                'cannot be scheduled because target register `{}` is not empty: '
                                'contains variable "{}".').format(self.name,
                                                                  self.id,
                                                                  target_register.name,
                                                                  target_register.contained_variable.name))

        assert not target_register.contained_variable or self.__dummy_var == target_register.contained_variable
        # Perform the move
        register_dirty = variable.register_dirty
        source_register = variable.register
        target_register.allocateVariable(variable)
        source_register.allocateVariable(self.__dummy_var)  # Mark source register as free for next bundle
        assert source_register.bank.bank_index == 0
        # Swap source and dest to keep the output format of the string instruction consistent
        self.sources[0] = source_register
        self.dests[0] = variable

        retval = super()._schedule(cycle_count, schedule_id)
        # We only moved the variable, we didn't change its value
        variable.register_dirty = register_dirty  # Preserve register dirty state

        if self.comment:
            self.comment += ';'
        self.comment += ' variable "{}"'.format(variable.name)

        return retval

    def _toPISAFormat(self, *extra_args) -> str:
        """
        This instruction has no PISA equivalent.

        Parameters:
            extra_args: Additional arguments (not used).

        Returns:
            None: As there is no PISA equivalent for this instruction.
        """
        return None

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

        return super()._toXASMISAFormat()