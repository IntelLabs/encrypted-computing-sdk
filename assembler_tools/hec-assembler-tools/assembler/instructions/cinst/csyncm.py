import warnings

from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates a `csyncm` CInstruction.

    This instruction is used to synchronize with a specific instruction from the MINST queue.

    For more information, check the `csyncm` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_csyncm.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'csyncm'.
        """
        return "csyncm"

    def __init__(self,
                 id: int,
                 minstr,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `csyncm` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            minstr: MInstruction
                Instruction from the MINST queue for which to wait.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.minstr = minstr # Instruction from the MINST queue for which to wait

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, minstr, throughput, and latency.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'minstr={}, '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                        self.name,
                                                        hex(id(self)),
                                                        self.id,
                                                        repr(self.minstr),
                                                        self.throughput,
                                                        self.latency)
        return retval

    def _set_dests(self, value):
        """
        Raises an error as the instruction does not have destination operands.

        Parameters:
            value: The value to set as destination, which is not applicable.

        Raises:
            RuntimeError: Always raised as the instruction does not have parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _set_sources(self, value):
        """
        Raises an error as the instruction does not have source operands.

        Parameters:
            value: The value to set as source, which is not applicable.

        Raises:
            RuntimeError: Always raised as the instruction does not have parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: MInstruction to sync is invalid or has not been scheduled.
                See inherited for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        if not self.minstr:
            raise RuntimeError("Invalid empty MInstruction.")
        if not self.minstr.is_scheduled:
            raise RuntimeError("MInstruction to sync is not scheduled yet.")

        retval = super()._schedule(cycle_count, schedule_id)
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
        assert(self.minstr.is_scheduled)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # warnings.warn("`csyncm` instruction requires second pass to set correct instruction number.")
        return super()._toCASMISAFormat(self.minstr.schedule_timing.index)