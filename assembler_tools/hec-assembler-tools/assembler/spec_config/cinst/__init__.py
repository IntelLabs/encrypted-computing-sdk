from .. import ISASpecInstruction

class BLoad(ISASpecInstruction):
    """
    Represents a `bload` instruction.

    This instruction loads metadata from scratchpad to register file.

    For more information, check the `bload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bload.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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
            int: The latency, which is 5.
        """
        return 5

class BOnes(ISASpecInstruction):
    """
    Represents a `bones` instruction.

    The `bones` instruction loads metadata of identity (one) from the scratchpad to the register file.
    
    For more information, check the `bones` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_bones.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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
            int: The latency, which is 5.
        """
        return 5

class Exit(ISASpecInstruction):
    """
    Represents an `cexit` instruction.

    This instruction terminates execution of a HERACLES program.

    For more information, check the `cexit` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cexit.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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

class CLoad(ISASpecInstruction):
    """
    Represents a `cload` instruction.

    This instruction loads a single polynomial residue from scratchpad into a register.

    For more information, check the `cload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cload.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 1.
        """
        return 1

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 1.
        """
        return 1

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 4.
        """
        return 4

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 4.
        """
        return 4

class Nop(ISASpecInstruction):
    """
    Represents a `nop` instruction.

    This instruction adds desired amount of idle cycles in the Cfetch flow.

    For more information, check the `nop` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nop.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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

class CStore(ISASpecInstruction):
    """
    Represents a `cstore` instruction.

    This instruction fetchs a single polynomial residue from the intermediate data buffer and store back to SPAD.

    For more information, check the `cstore` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_cstore.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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
            int: The latency, which is 5.
        """
        return 5

class CSyncM(ISASpecInstruction):
    """
    Represents a `csyncm` instruction.

    Wait instruction similar to a barrier that stalls the execution of CINST
    queue until the specified instruction from MINST queue has completed.

    For more information, check the `csyncm` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_csyncm.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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

class iFetch(ISASpecInstruction):
    """
    Represents an `ifetch` instruction.

    This instruction fetchs a bundle of instructions from the XINST queue and send it to the CE for execution.

    For more information, check the `ifetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_ifetch.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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
            int: The latency, which is 5.
        """
        return 5

class KGLoad(ISASpecInstruction):
    """
    Represents a `kgload` instruction.
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 1.
        """
        return 1

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 0.
        """
        return 0

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 4.
        """
        return 4

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 40.
        """
        return 40

class KGSeed(ISASpecInstruction):
    """
    Represents a `kgseed` instruction.
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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

class KGStart(ISASpecInstruction):
    """
    Represents a `kgstart` instruction.
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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
            int: The latency, which is 40.
        """
        return 40

class NLoad(ISASpecInstruction):
    """
    Represents a `nload` instruction.

    This instruction loads metadata (for NTT/iNTT routing mapping) from
    scratchpad into a special routing table register.

    For more information, check the `nload` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_nload.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 1.
        """
        return 1

    @classmethod
    def _get_throughput(cls) -> int:
        """
        Gets the throughput of the instruction.

        Returns:
            int: The throughput, which is 4.
        """
        return 4

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 4.
        """
        return 4

class XInstFetch(ISASpecInstruction):
    """
    Represents an `xinstfetch` instruction.

    Fetches instructions from the HBM and sends it to the XINST queue.

    For more information, check the `xinstfetch` Specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/cinst/cinst_xinstfetch.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 0.
        """
        return 0

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

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