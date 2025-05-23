
from assembler.common.config import GlobalConfig
from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable, DummyVariable
from assembler.memory_model.register_file import Register

class Instruction(CInstruction):
    """
    Encapsulates a `cstore` CInstruction.

    A `cstore` instruction pops the top word from the intermediate data buffer queue
    and stores it in SPAD. To accomplish this in scheduling, a `cstore` should
    be scheduled immediately after the `ifetch` for the bundle containing the matching
    `xstore`.
    
    For more information, check the `cstore` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cstore.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'cstore'.
        """
        return "cstore"

    def __init__(self,
                 id: int,
                 mem_model: MemoryModel,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `cstore` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            mem_model (MemoryModel): The memory model containing the SPAD where to store the source variable.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `mem_model` is not an instance of `MemoryModel`.
        """
        if not isinstance(mem_model, MemoryModel):
            raise ValueError('`mem_model` must be an instance of `MemoryModel`.')
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.__mem_model = mem_model
        self.__spad_addr = -1

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, throughput, and latency.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Sets the destination variables for the instruction.

        Parameters:
            value (list): A list of `Variable` objects to set as destinations.

        Raises:
            ValueError: If the number of destinations is incorrect or if the list does not contain `Variable` objects.
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
        Sets the source registers for the instruction.

        Parameters:
            value (list): A list of `Register` objects to set as sources.

        Raises:
            ValueError: If the number of sources is incorrect.
            TypeError: If the list does not contain `Register` objects.
        """
        if len(value) != Instruction._OP_NUM_SOURCES:
            raise ValueError(("`value`: Expected list of {} `Register` objects, "
                              "but list with {} elements received.".format(Instruction._OP_NUM_DESTS,
                                                                           len(value))))
        if not all(isinstance(x, Register) for x in value):
            raise TypeError("`value`: Expected list of `Register` objects.")
        super()._set_sources(value)

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Source Variable and its Register will be updated to reflect the store.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): The schedule ID for the instruction.

        Raises:
            RuntimeError: When one of the following happens:
                - Source and destination are not the same variable.
                - Source is not on a register.
                See inherited for more exceptions.

            ValueError: Invalid arguments or either double or conflicting allocations.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        spad = self.__mem_model.spad

        var_name, (variable, self.__spad_addr) = self.__mem_model.store_buffer.pop() # Will raise IndexError if popping from empty queue
        assert(var_name == variable.name)
        assert self.__spad_addr >= 0 and (variable.spad_address < 0 or variable.spad_address == self.__spad_addr), \
               f'self.__spad_addr = {self.__spad_addr}; {variable.name}.spad_address = {variable.spad_address}'

        retval = super()._schedule(cycle_count, schedule_id)
        # Perform the cstore
        if spad.buffer[self.__spad_addr] and spad.buffer[self.__spad_addr] != variable:
            if not isinstance(spad.buffer[self.__spad_addr], DummyVariable):
                raise RuntimeError(f'SPAD location {self.__spad_addr} for instruction (`{self.name}`, id {self.id}) is occupied by variable {spad.buffer[self.__spad_addr]}.')
            spad.deallocate(self.__spad_addr)
        spad.allocateForce(self.__spad_addr, variable) # Allocate in SPAD
        # Track last access to SPAD address
        spad_access_tracking = spad.getAccessTracking(self.__spad_addr)
        spad_access_tracking.last_cstore = self
        spad_access_tracking.last_mload = None # Last mload is now obsolete
        variable.spad_dirty = True # Variable has new value in SPAD
        
        if not GlobalConfig.hasHBM:
            # Used to track the variable name going into spad at the moment of cstore.
            # This is used to output var name instead of spad address when requested.
            # remove when we have spad and HBM back
            self.__spad_addr = variable.toCASMISAFormat()

        if self.comment:
            self.comment += ';'
        self.comment += f' {variable.name}'
        return retval

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        See inherited for more information.

        Parameters:
            extra_args (tuple): Additional arguments, which are not supported.

        Returns:
            str: The instruction in CInst ASM-ISA format.

        Raises:
            ValueError: If extra arguments are provided.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toCASMISAFormat(self.__spad_addr)