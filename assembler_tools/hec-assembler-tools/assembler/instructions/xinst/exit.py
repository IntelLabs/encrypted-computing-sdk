from .xinstruction import XInstruction

class Instruction(XInstruction):
    """
    Represents a `bexit` instruction in the assembler with specific properties and methods for
    scheduling and formatting.

    This instruction terminates execution of an instruction bundle.

    For more information, check the specificationn:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_exit.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: The operation name in ASM format.
        """
        return "bexit"

    def __init__(self,
                 id: int,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Initializes an Instruction object with the given parameters.

        Parameters:
            id (int): The unique identifier for the instruction.
            throughput (int, optional): The throughput of the instruction. Defaults to None.
            latency (int, optional): The latency of the instruction. Defaults to None.
            comment (str, optional): A comment associated with the instruction. Defaults to an empty string.
        """
        if not throughput:
            throughput = Instruction._OP_DEFAULT_THROUGHPUT
        if not latency:
            latency = Instruction._OP_DEFAULT_LATENCY
        N = 0
        super().__init__(id, N, throughput, latency, comment=comment)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation.
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
        Raises an error as `bexit` does not have destination parameters.

        Parameters:
            value: The value to set as destinations.

        Raises:
            RuntimeError: Always raised as `bexit` does not have parameters.
        """
        raise RuntimeError(f"Instruction `{self.OP_NAME_PISA}` does not have parameters.")

    def _set_sources(self, value):
        """
        Raises an error as `bexit` does not have source parameters.

        Parameters:
            value: The value to set as sources.

        Raises:
            RuntimeError: Always raised as `bexit` does not have parameters.
        """
        raise RuntimeError(f"Instruction `{self.OP_NAME_PISA}` does not have parameters.")

    def _toPISAFormat(self, *extra_args) -> str:
        """
        This instruction has no PISA equivalent.

        Parameters:
            *extra_args: Additional arguments (not supported).

        Returns:
            None: As this instruction has no PISA equivalent.
        """
        return None

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            *extra_args: Additional arguments (not supported).

        Raises:
            ValueError: If extra arguments are provided.

        Returns:
            str: The instruction in ASM format.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        return super()._toXASMISAFormat()