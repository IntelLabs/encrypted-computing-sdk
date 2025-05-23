from assembler.common.cycle_tracking import CycleType
from .minstruction import MInstruction
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable

class Instruction(MInstruction):
    """
    Encapsulates an `mstore` MInstruction.

    Instruction `mstore` stores a word, corresponding to a single polynomial residue,
    from SPAD memory into HBM data region.

    MINST queue should use `msyncc` before scheduling this instruction to ensure source
    SPAD address is ready.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mstore.md

    Attributes:
        dst_hbm_addr (int): HBM address where to store the source variable.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'mstore'.
        """
        return "mstore"

    def __init__(self,
                 id: int,
                 src: list,
                 mem_model: MemoryModel,
                 dst_hbm_addr: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `mstore` MInstruction.

        SPAD should use `csyncm` matching this instruction before using the address.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            src (list of Variable): A list containing a single Variable object indicating the source variable to store from
                                    SPAD into HBM.

            mem_model (MemoryModel): The memory model containing the SPAD where to store the source variable.

            dst_hbm_addr (int): HBM address where to store the source variable.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `dst_hbm_addr` is negative.
        """
        if dst_hbm_addr < 0:
            raise ValueError('`dst_hbm_addr`: cannot be null address (negative).')
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        super().__init__(id, throughput, latency, comment=comment)
        self.__mem_model = mem_model
        self.dst_hbm_addr = dst_hbm_addr
        self.__internal_set_dests(src)
        self._set_sources(src)
        self.__source_spad_address = src[0].spad_address

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, source, destination HBM address, throughput, and latency.
        """
        assert(len(self.dests) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'src={}, dst_hbm_addr={}, mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.sources,
                                                           self.dst_hbm_addr,
                                                           # repr(self.__mem_model),
                                                           self.throughput,
                                                           self.latency)
        return retval

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

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Source Variable will be updated to reflect the load.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: Multiple SPAD allocation or source is not allocated to HBM.
                See inherited method for other exceptions.

            ValueError: Invalid SPAD address.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        assert(Instruction._OP_NUM_SOURCES > 0 and len(self.sources) == Instruction._OP_NUM_SOURCES)
        assert(Instruction._OP_NUM_DESTS > 0 and len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(all(src == dst for src, dst in zip(self.sources, self.dests)))

        hbm = self.__mem_model.hbm
        spad = self.__mem_model.spad

        variable: Variable = self.sources[0]
        if self.__source_spad_address < 0:
            self.__source_spad_address = self.sources[0].spad_address

        if variable.hbm_address >= 0:
            if self.dst_hbm_addr != variable.hbm_address:
                raise RuntimeError("Source variable is already in different HBM location. Cannot store a variable into HBM more than once.")
            assert(hbm.buffer[variable.hbm_address] == variable)
        if self.__source_spad_address < 0:
            raise RuntimeError("Null reference exception: source variable is not in SPAD.")

        if self.comment:
            self.comment += ';'
        # self.comment += ' variable "{}": HBM({}) <- SPAD({})'.format(variable.name,
        #                                                              self.dst_hbm_addr,
        #                                                              variable.spad_address)
        self.comment += ' variable "{}" <- SPAD({})'.format(variable.name,
                                                            variable.spad_address)

        retval = super()._schedule(cycle_count, schedule_id)
        # Perform the store
        if variable.hbm_address < 0: # Variable new to HBM
            hbm.allocateForce(self.dst_hbm_addr, variable)
        spad.deallocate(self.__source_spad_address) # Deallocate variable from SPAD
        # Track SPAD access
        spad_access_tracking = spad.getAccessTracking(self.__source_spad_address)
        spad_access_tracking.last_mstore = self
        # No need to track last CInst access after a `mstore`
        spad_access_tracking.last_cload = None
        spad_access_tracking.last_cstore = None

        return retval

    def _toMASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to MInst ASM-ISA format.

        See inherited for more information.

        Parameters:
            extra_args: Additional arguments for formatting.

        Returns:
            str: The instruction in MInst ASM-ISA format.
        """
        # Instruction sources
        extra_args = (self.__source_spad_address, ) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toMASMISAFormat() for dst in self.dests) + extra_args
        return self.toStringFormat(None,
                                   self.OP_NAME_ASM,
                                   *extra_args)