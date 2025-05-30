from .. import ISASpecInstruction

class MLoad(ISASpecInstruction):
    """
    Represents an `mload` instruction, inheriting from ISASpecInstruction.

    This instruction loads a single polynomial residue from local memory to scratchpad.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mload.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands for the instruction.

        Returns:
            int: The number of destination operands, which is 1.
        """
        return 1

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands for the instruction.

        Returns:
            int: The number of source operands, which is 1.
        """
        return 1

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 1.
        """
        return 1

class MStore(ISASpecInstruction):
    """
    Represents an `mstore` instruction, inheriting from ISASpecInstruction.

    This instruction stores a single polynomial residue from scratchpad to local memory.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_mstore.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands for the instruction.

        Returns:
            int: The number of destination operands, which is 1.
        """
        return 1

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands for the instruction.

        Returns:
            int: The number of source operands, which is 1.
        """
        return 1

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 1.
        """
        return 1

class MSyncC(ISASpecInstruction):
    """
    Represents an MSyncC instruction, inheriting from ISASpecInstruction.

    Wait instruction similar to a barrier that stalls the execution of MINST
    queue until the specified instruction from CINST queue has completed.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/minst/minst_msyncc.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands for the instruction.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands for the instruction.

        Returns:
            int: The number of source operands, which is 0.
        """
        return 0

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 1.
        """
        return 1