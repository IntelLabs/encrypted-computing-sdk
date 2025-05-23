
from .cinstruction import CInstruction

class Instruction(CInstruction):
    """
    Represents a 'cnop' CInstruction from the ASM ISA specification.

    This class is used to create a 'cnop' instruction, which is a type of 
    no-operation (NOP) instruction that inserts a specified number of idle 
    cycles during its execution. The instruction does not have any destination 
    or source operands.

    For more information, check the `cnop` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nop.md
    """

    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the ASM name of the operation.

        Returns:
            str: The name of the operation in ASM format, which is 'cnop'.
        """
        return "cnop"

    def __init__(self,
                 id: int,
                 idle_cycles: int,
                 comment: str = ""):
        """
        Constructs a new 'cnop' CInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled 
                      with a nonce to form a unique ID.
            idle_cycles (int): Number of idle cycles to insert in the CInst execution.
            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        # Throughput and latency for 'nop' is the number of idle cycles
        super().__init__(id, idle_cycles, idle_cycles, comment=comment)

    def __repr__(self):
        """
        Returns a string representation of the Instruction object.

        Returns:
            str: A string representation of the Instruction object, including 
                 its type, name, memory address, ID, and throughput.
        """
        retval=('<{}({}) object at {}>(id={}[0], '
                  'idle_cycles={})').format(type(self).__name__,
                                            self.name,
                                            hex(id(self)),
                                            self.id,
                                            self.throughput)
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

    def _toCASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM format.

        Parameters:
            extra_args: Additional arguments, which are not supported.

        Returns:
            str: The instruction in ASM format.

        Raises:
            AssertionError: If the number of destinations or sources is incorrect.
            ValueError: If extra arguments are provided.
        """
        assert(len(self.dests) == Instruction._OP_NUM_DESTS)
        assert(len(self.sources) == Instruction._OP_NUM_SOURCES)

        if extra_args:
            raise ValueError('`extra_args` not supported.')

        # The idle cycles in the ASM ISA for 'nop' must be one less because decoding/scheduling
        # the instruction counts as a cycle.
        return super()._toCASMISAFormat(self.throughput - 1)