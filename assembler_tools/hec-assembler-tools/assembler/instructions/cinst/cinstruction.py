from assembler.common.cycle_tracking import CycleType
from ..instruction import BaseInstruction

class CInstruction(BaseInstruction):
    """
    Represents a CInstruction, which is a type of BaseInstruction.

    This class provides the basic structure and functionality for CInstructions, including
    methods for converting to CInst ASM-ISA format.

    Attributes:
        id (int): User-defined ID for the instruction.
        throughput (int): The throughput of the instruction.
        latency (int): The latency of the instruction.
        comment (str): An optional comment for the instruction.
    """

    # Constructor
    # -----------

    def __init__(self,
                 id: int,
                 throughput : int,
                 latency : int,
                 comment: str = ""):
        """
        Constructs a new CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            throughput (int): The throughput of the instruction.
            latency (int): The latency of the instruction.
            comment (str, optional): An optional comment for the instruction.
        """
        super().__init__(id, throughput, latency, comment=comment)


    # Methods and properties
    # ----------------------

    def _get_cycle_ready(self):
        """
        Returns the cycle ready value for the instruction.

        This method overrides the base method to provide a specific cycle ready value for CInstructions.

        Returns:
            CycleType: A CycleType object with bundle and cycle set to 0.
        """
        return CycleType(bundle = 0, cycle = 0)

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        This method constructs the ASM-ISA format string for the instruction by combining
        the instruction's sources and destinations with any additional arguments.

        Parameters:
            extra_args: Additional arguments for the conversion.

        Returns:
            str: The CInst ASM-ISA format string of the instruction.
        """

        preamble = []
        # instruction sources
        extra_args = tuple(src.toCASMISAFormat() for src in self.sources) + extra_args
        # instruction destinations
        extra_args = tuple(dst.toCASMISAFormat() for dst in self.dests) + extra_args
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)
