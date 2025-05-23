from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Represents a `cexit` CInstruction.

    This instruction terminates execution of a HERACLES program.

    For more information, check the `cexit` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cexit.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name for the operation.

        Returns:
            str: The ASM name for the operation, which is "cexit".
        """
        return "cexit"

    def __init__(self,
                 id: int,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Constructs a new `cexit` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            throughput (int, optional): The throughput of the instruction. Defaults to the class-defined throughput.
            latency (int, optional): The latency of the instruction. Defaults to the class-defined latency.
            comment (str, optional): An optional comment for the instruction.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        super().__init__(id, throughput, latency, comment=comment)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'throughput={}, latency={})').format(type(self).__name__,
                                                           self.name,
                                                           hex(id(self)),
                                                           self.id,
                                                           self.throughput,
                                                           self.latency)
        return retval

    def _set_dests(self, value):
        """
        Raises an error as the `cexit` instruction does not have destination parameters.

        Parameters:
            value: The value to set as destinations.

        Raises:
            RuntimeError: Always, as `cexit` does not have destination parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _set_sources(self, value):
        """
        Raises an error as the `cexit` instruction does not have source parameters.

        Parameters:
            value: The value to set as sources.

        Raises:
            RuntimeError: Always, as `cexit` does not have source parameters.
        """
        raise RuntimeError(f"Instruction `{self.name}` does not have parameters.")

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            extra_args: Additional arguments for the conversion.

        Raises:
            ValueError: If `extra_args` are provided.

        Returns:
            str: The ASM format string of the instruction.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toCASMISAFormat()
