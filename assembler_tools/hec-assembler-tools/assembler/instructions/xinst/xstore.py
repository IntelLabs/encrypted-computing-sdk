from assembler.common.cycle_tracking import CycleType
from .xinstruction import XInstruction
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable

class Instruction(XInstruction):
    """
    Encapsulates an `xstore` MInstruction.

    Instruction `xstore` transfers a word from a CE register into the intermediate data
    buffer. The intermediate data buffer features a FIFO structure, which means that the
    transferred data is pushed at the end of the queue.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_xstore.md
        
    Attributes:
        dest_spad_address (int): The SPAD address where the source variable will be stored.

    Methods:
        reset_GlobalCycleReady: Resets the global cycle ready for `xstore` instructions.
    """

    __xstore_global_cycle_ready = CycleType(0, 0) # private class attribute to track cycle ready among xstores

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'xstore'.
        """
        return "xstore"

    def __init__(self,
                 id: int,
                 src: list,
                 mem_model: MemoryModel,
                 dest_spad_addr: int = -1,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `xstore` MInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            src (list of Variable): A list containing a single Variable object indicating the source variable to store into SPAD.
                                    Variable must be assigned to a register.
                                    Variable `spad_address` must be negative (not assigned) or match the address of the corresponding
                                    `cstore` instruction.

            mem_model (MemoryModel): The memory model used for storing the source variable.

            dest_spad_addr (int, optional): The SPAD address where the source variable will be stored. Defaults to -1.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `mem_model` is not an instance of `MemoryModel` or if `dest_spad_addr` is invalid.
        """
        if not isinstance(mem_model, MemoryModel):
            raise ValueError('`mem_model` must be an instance of `MemoryModel`.')
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        N = 0 # Does not require ring-size
        super().__init__(id, N, throughput, latency, comment=comment)
        self.__mem_model = mem_model
        self._set_sources(src)
        self.__internal_set_dests(src)

        if dest_spad_addr < 0 and src[0].spad_address < 0:
            raise ValueError('`dest_spad_addr` must be a valid SPAD address if source variable is not allocated in SPAD.')
        if dest_spad_addr >= 0 and src[0].spad_address >= 0 and dest_spad_addr != src[0].spad_address:
            raise ValueError('`dest_spad_addr` must be null SPAD address (negative) if source variable is allocated in SPAD.')
        self.dest_spad_address = src[0].spad_address if dest_spad_addr < 0 else dest_spad_addr

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, source, memory model, destination SPAD address, throughput, and latency.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'src={}, mem_model, dest_spad_addr={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.dests,
                                                           self.dest_spad_address,
                                                           self.throughput,
                                                           self.latency)
        return retval

    @classmethod
    def __set_xstoreGlobalCycleReady(cls, value: CycleType):
        """
        Sets the global cycle ready for xstore instructions.

        Parameters:
            value (CycleType): The cycle type value to set.
        """
        if (value > cls.__xstore_global_cycle_ready):
            cls.__xstore_global_cycle_ready = value

    @classmethod
    def reset_GlobalCycleReady(cls, value=CycleType(0, 0)):
        """
        Resets the global cycle ready for xstore instructions.

        Parameters:
            value (CycleType, optional): The cycle type value to reset to. Defaults to CycleType(0, 0).
        """
        cls.__xstore_global_cycle_ready = value

    def _set_dests(self, value):
        """
        Raises an error as the instruction only supports setting sources.

        Parameters:
            value: The value to set as destination, which is not applicable.

        Raises:
            RuntimeError: Always raised as the instruction only supports setting sources.
        """
        raise RuntimeError(f"Instruction `{self.name}` only supports setting sources.")

    def __internal_set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): A list of `Variable` objects to set as destinations.

        Raises:
            ValueError: If the number of destinations is incorrect.
            TypeError: If the list does not contain `Variable` objects.
        """
        if len(value) != Instruction._OP_NUM_DESTS:
            raise ValueError(("`value`: Expected list of {} `Variable` objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_SOURCES,
                                                                           len(value))))
        if not all(isinstance(x, Variable) for x in value):
            raise ValueError("`value`: Expected list of `Variable` objects.")
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
        self.__internal_set_dests(value)

    def _get_cycle_ready(self):
        """
        Returns the current value for ready cycle.

        Overrides :func:`BaseInstruction._get_cycle_ready`.

        Returns:
            CycleType: The maximum cycle ready among this instruction's sources and the global cycles-ready for other xstores.
        """
        # This will return the maximum cycle ready among this instruction
        # sources and the global cycles-ready for other xstores.
        # An xstore cannot be within _OP_DEFAULT_LATENCY cycles from another xstore
        # because they both use the SPAD-CE data channel.
        return max(super()._get_cycle_ready(),
                   Instruction.__xstore_global_cycle_ready)

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Scheduling `xstore` XInst will not cause the involved registers and variables to be
        updated. Scheduling a `xstore` should be accompanied with the scheduling of a matching
        CInst `cstore` to occur immediately after this `xstore`'s bundle is fetched by `ifetch`.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: If the source is not a `Variable` or if the instruction is already scheduled.
                See inherited method for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)
        assert(Instruction._OP_NUM_DESTS > 0 and len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(all(src == dst for src, dst in zip(self.sources, self.dests)))

        if not isinstance(self.sources[0], Variable):
            raise RuntimeError('XInstruction ({}, id = {}) already scheduled.'.format(self.name, self.id))
        
        store_buffer_item = MemoryModel.StoreBufferValueType(variable=self.sources[0],
                                                             dest_spad_address=self.dest_spad_address)
        register = self.sources[0].register
        retval = super()._schedule(cycle_count, schedule_id)
        # Perform xstore
        register.register_dirty = False # Register has been flushed
        register.allocateVariable(None)
        self.sources[0] = register # Make the register the source for freezing, since variable is no longer in it
        self.__mem_model.store_buffer[store_buffer_item.variable.name] = store_buffer_item
        # Matching CInst cstore completes the xstore

        if self.comment:
            self.comment += ';'
        self.comment += ' variable "{}": SPAD({}) <- {}'.format(store_buffer_item.variable.name,
                                                                store_buffer_item.dest_spad_address,
                                                                register.name)

        # Set the global cycle ready for next xstore
        Instruction.__set_xstoreGlobalCycleReady(CycleType(cycle_count.bundle, cycle_count.cycle + self.latency))
        return retval

    def _toPISAFormat(self, *extra_args) -> str:
        """
        This instruction has no PISA equivalent.

        Returns:
            None
        """
        return None

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM-ISA format.

        Parameters:
            extra_args: Variable number of arguments to add before the residual in the resulting string.

        Returns:
            str: A string representation of the instruction in ASM-ISA format. The string has the form:
                 `id[0], N, xstore, dst_spad_addr, src_register, res=0 [# comment]`
                 Since the residual is mandatory in the format, it is set to `0` in the output if the
                 instruction does not support residual.
                 `dst_spad_addr` may be ignored as it is for bookkeeping purposes only.

        Raises:
            ValueError: If extra arguments are provided.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        preamble = (self.id[0],)
        # Instruction sources
        extra_args = tuple(src.toXASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        # extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        # extra_args += (0,) # res = 0
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)