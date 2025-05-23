from assembler.common.cycle_tracking import CycleType
from .cinstruction import CInstruction
from assembler.memory_model.variable import Variable

class Instruction(CInstruction):
    """
    Encapsulates `kg_start` CInstruction.

    `kg_start` instruction signals the keygen engine to start producing key material
    using the currently loaded seed.

    Rules:
    1. `kg_load`s and `kg_start`s must be `latency` cycles apart from any other
    `kg_load` and `kg_start`. It takes between 10 to `latency` cycles for the key generation
    resource to generate the next key material, possibly causing contention if
    the key material is requested by any `kg_load` within `latency` cycles.
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'kg_start'.
        """
        return "kg_start"

    def __init__(self,
                 id: int,
                 throughput: int = None,
                 latency: int = None,
                 comment: str = ""):
        """
        Constructs a new `kg_start` CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            throughput (int, optional): The throughput of the instruction. Defaults to the class's default throughput.

            latency (int, optional): The latency of the instruction. Defaults to the class's default latency.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
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
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, throughput, and latency.
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

        return super()._toCASMISAFormat()