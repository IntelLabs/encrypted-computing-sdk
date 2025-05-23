from assembler.common.cycle_tracking import CycleType
from .minstruction import MInstruction

class Instruction(MInstruction):
    """
    Encapsulates an `msyncc` MInstruction.

    This instruction is used to synchronize with a specific instruction from the CINST queue.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_msyncc.md

    Attributes:
        cinstr: The instruction from the CINST queue for which to wait.
    """
    
    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'msyncc'.
        """
        return "msyncc"

    def __init__(self,
                 id: int,
                 cinstr,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `msyncc` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            cinstr: CInstruction
                Instruction from the CINST queue for which to wait.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.cinstr = cinstr # Instruction number from the MINST queue for which to wait

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, cinstr, throughput, and latency.
        """
        assert(len(self.dests) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'cinstr={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.OP_NAME_PISA,
                                                           hex(id(self)),
                                                           self.id,
                                                           repr(self.cinstr),
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
        Raises an error as the instruction does not have source parameters.

        Parameters:
            value: The value to set as source, which is not applicable.

        Raises:
            RuntimeError: Always raised as the instruction does not have source parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: CInstruction to sync is invalid or has not been scheduled.
                See inherited for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        if not self.cinstr:
            raise RuntimeError("Invalid empty CInstruction.")
        if not self.cinstr.is_scheduled:
            raise RuntimeError("CInstruction to sync is not scheduled yet.")

        retval = super()._schedule(cycle_count, schedule_id)
        return retval

    def _toMASMISAFormat(self, *extra_args) -> str:
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
        assert(self.cinstr.is_scheduled)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # warnings.warn("`msyncc` instruction requires second pass to set correct instruction number.")
        return super()._toMASMISAFormat(self.cinstr.schedule_timing.index)