from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents a `nop` (no operation) instruction in an assembly language.

    This class handles the representation and conversion of `nop` instructions,
    which are used to introduce idle cycles in the execution pipeline.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_nop.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: The operation name as a string.
        """
        return "nop"

    def __init__(self,
                 id: int,
                 idle_cycles: int,
                 comment: str = ""):
        """
        Initializes an Instruction object for a 'nop' operation.

        Parameters:
            id (int): The unique identifier for the instruction.
            idle_cycles (int): The number of idle cycles for the 'nop' operation.
            comment (str, optional): An optional comment for the instruction.
        """
        N = 0
        # Throughput and latency for `nop` is the number of idle cycles
        super().__init__(id, N, idle_cycles, idle_cycles, comment=comment)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the object.
        """
        retval = ('<{}({}) object at {}>(id={}[0], '
                  'idle_cycles={})').format(type(self).__name__,
                                            self.name,
                                            hex(id(self)),
                                            self.id,
                                            self.throughput)
        return retval

    def _set_dests(self, value):
        """
        Raises an error as 'nop' instruction does not have destination parameters.

        Parameters:
            value: The value to set as destinations (not used).

        Raises:
            RuntimeError: Always raised as 'nop' has no parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _set_sources(self, value):
        """
        Raises an error as 'nop' instruction does not have source parameters.

        Parameters:
            value: The value to set as sources (not used).

        Raises:
            RuntimeError: Always raised as 'nop' has no parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _toPISAFormat(self, *extra_args) -> str:
        """
        Indicates that this instruction has no PISA equivalent.

        Parameters:
            extra_args: Additional arguments (not used).

        Returns:
            None: As there is no PISA equivalent for 'nop'.
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

        # The idle cycles in the ASM ISA for `nop` must be one less because decoding/scheduling
        # the instruction counts as a cycle.
        return super()._toXASMISAFormat(self.throughput - 1)