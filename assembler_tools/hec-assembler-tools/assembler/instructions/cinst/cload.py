
from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable
from assembler.memory_model.register_file import Register

class Instruction(CInstruction):
    """
    Encapsulates a `cload` CInstruction.

    A `cload` instruction loads a word, corresponding to a single polynomial residue,
    from scratchpad memory into the register file memory.
    
    For more information, check the `cload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cload.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name for the operation.

        Returns:
            str: The ASM name for the operation, which is "cload".
        """
        return "cload"

    def __init__(self,
                 id: int,
                 dst: Register,
                 src: list,
                 mem_model: MemoryModel,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Constructs a new `cload` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            dst (Register): The destination register where to load the variable in `src`.
            src (list): A list containing a single Variable object indicating the source variable to store from
                register into SPAD.
            mem_model (MemoryModel): The memory model containing the SPAD where to store the source variable.
            throughput (int, optional): The throughput of the instruction. Defaults to the class-defined throughput.
            latency (int, optional): The latency of the instruction. Defaults to the class-defined latency.
            comment (str, optional): An optional comment for the instruction.

        Raises:
            AssertionError: If the destination register bank index is not 0.
        """
        assert(dst.bank.bank_index == 0) # We must be following convention of loading from SPAD into bank 0
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.__mem_model = mem_model
        self._set_dests([ dst ])
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object.
        """
        assert(len(self.dests) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'dst={}, src={},'
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.dests[0],
                                                           self.sources,
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Validates and sets the list of destination registers.

        Parameters:
            value (list): The list of destination registers to set.

        Raises:
            ValueError: If the value is not a list of the expected number of `Register` objects.
            TypeError: If the value is not a list of `Register` objects.
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
        Validates and sets the list of source variables.

        Parameters:
            value (list): The list of source variables to set.

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

        Source Variable and destination Register will be updated to reflect the load.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_id (int): The schedule ID for the instruction.

        Raises:
            RuntimeError: If the variable or register is already allocated, or if other exceptions occur.

        Returns:
            int: The throughput for this instruction, i.e., the number of cycles by which to advance
            the current cycle counter.
        """
        assert(Instruction._OP_NUM_DESTS > 0 and len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)

        variable: Variable = self.sources[0] # Expected sources to contain a Variable
        target_register: Register = self.dests[0]

        if variable.spad_address < 0:
            raise RuntimeError(f"Null Access Violation: Variable `{variable}` not allocated in SPAD.")
        # Cannot allocate variable to more than one register (memory coherence)
        # and must not overrite a register that already contains a variable.
        if variable.register:
            raise RuntimeError(f"Variable `{variable}` already allocated in register `{variable.register}`.")
        if target_register.contained_variable:
            raise RuntimeError(f"Register `{target_register}` already contains a Variable object.")

        retval = super()._schedule(cycle_count, schedule_id)
        # Perform the load
        target_register.allocateVariable(variable)
        # Track last access to SPAD address
        spad_access_tracking = self.__mem_model.spad.getAccessTracking(variable.spad_address)
        spad_access_tracking.last_cload = self
        # No need to sync to any previous MLoads after cload
        spad_access_tracking.last_mload = None

        if self.comment:
            self.comment += ';'
        self.comment += f' {variable.name}'

        return retval
