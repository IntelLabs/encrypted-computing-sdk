from assembler.common import constants
from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Encapsulates an `xinstfetch` CInstruction.

    `xinstfetch` fetches 1 word (32KB) worth of instructions from the HBM XInst
    region and sends it to the XINST queue.

    For more information, check the `xinstfetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_xinstfetch.md

    Attributes:
        xq_dst (int): Destination word address in XINST queue in the range
                      [0, constants.MemoryModel.XINST_QUEUE_MAX_CAPACITY_WORDS).

        hbm_src (int): Address of the word worth of instructions in HBM XInst region to copy into XINST queue.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'xinstfetch'.
        """
        return "xinstfetch"

    def __init__(self,
                 id: int,
                 xq_dst: int,
                 hbm_src: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `xinstfetch` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            xq_dst (int): Destination word address in XINST queue in the range [0, 32). XINST queue capacity is
                          32 words (1MB).

            hbm_src (int): Address of the word worth of instructions in HBM XInst region to copy into XINST queue.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)
        self.xq_dst = xq_dst
        self.hbm_src = hbm_src

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, xq_dst, hbm_src, throughput, and latency.
        """
        assert(len(self.dests) > 0)
        retval=('<{}({}) object at {}>(id={}[0], '
                  'xq_dst={}, hbm_src={},'
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.xq_dst,
                                                           self.hbm_src,
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
            RuntimeError: If the xq_dst is out of range or if the hbm_src is negative.
                See inherited for more exceptions.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        if self.xq_dst < 0 or self.xq_dst >= constants.MemoryModel.XINST_QUEUE_MAX_CAPACITY_WORDS:
            raise RuntimeError(('Invalid `xq_dst` XINST queue destination address. Expected value in range '
                                '[0, {}), but received {}.'. format(constants.MemoryModel.XINST_QUEUE_MAX_CAPACITY_WORDS,
                                                                     self.xq_dst)))
        if self.hbm_src < 0:
            raise RuntimeError("Invalid `hbm_src` negative HBM address.")

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

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toCASMISAFormat(self.xq_dst, self.hbm_src)