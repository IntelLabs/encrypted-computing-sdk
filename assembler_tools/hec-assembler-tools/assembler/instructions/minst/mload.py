
from assembler.common.config import GlobalConfig
from assembler.common.cycle_tracking import CycleType
from .minstruction import MInstruction
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable

class Instruction(MInstruction):
    """
    Encapsulates an `mload` MInstruction.

    Instruction `mload` loads a word, corresponding to a single polynomial residue,
    from HBM data region into the SPAD memory.

    CINST queue should use `csyncm` matching this instruction before using the address.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mload.md

    Attributes:
        dst_spad_addr (int): SPAD address where to load the source variable.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'mload'.
        """
        return "mload"

    def __init__(self,
                 id: int,
                 src: list,
                 mem_model: MemoryModel,
                 dst_spad_addr: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `mload` MInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            src (list of Variable): A list containing a single Variable object indicating the source variable to load from
                                    HBM into SPAD.

            mem_model (MemoryModel): The memory model containing the SPAD where to store the source variable.

            dst_spad_addr (int): SPAD address where to load the source variable.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY

        if not GlobalConfig.useHBMPlaceHolders:
            for variable in src:
                if comment:
                    comment += "; "
                comment += f'variable "{variable.name}"'

        super().__init__(id, throughput, latency, comment=comment)
        self.__mem_model = mem_model
        self.dst_spad_addr = dst_spad_addr
        self.__internal_set_dests(src)
        self._set_sources(src)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, source, destination SPAD address, throughput, and latency.
        """
        assert(len(self.dests) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'src={}, dst_spad_addr={}, mem_model, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.sources,
                                                           self.dst_spad_addr,
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

        if variable.spad_address >= 0:
            raise RuntimeError("Source variable is already in SPAD. Cannot load a variable into SPAD more than once.")
        if variable.hbm_address < 0:
            raise RuntimeError("Null reference exception: source variable is not in HBM.")

        retval = super()._schedule(cycle_count, schedule_id)
        # Perform the load
        spad.allocateForce(self.dst_spad_addr, variable)
        # Track SPAD access
        spad.getAccessTracking(self.dst_spad_addr).last_mload = self
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
        extra_args = tuple(src.toMASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        return self.toStringFormat(None,
                                   self.OP_NAME_ASM,
                                   *extra_args)