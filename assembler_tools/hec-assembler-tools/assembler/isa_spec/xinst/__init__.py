from assembler.common.decorators import *
from .. import ISASpecInstruction

class Add(ISASpecInstruction):
    """
    Represents an `add` instruction.

    This instructions adds two polynomials stored in the register file and
    store the result in a register.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_add.md
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
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 6.
        """
        return 6

class Copy(ISASpecInstruction):
    """
    Represents a Copy instruction.
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class Exit(ISASpecInstruction):
    """
    Represents an `exit` instruction.

    This instruction terminates execution of an instruction bundle.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_exit.md
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

class iNTT(ISASpecInstruction):
    """
    Represents an `intt` instruction.

    The Inverse Number Theoretic Transform (iNTT), converts NTT form to positional form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_intt.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 2.
        """
        return 2

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 3.
        """
        return 3

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
            int: The latency, which is 6.
        """
        return 6

class irShuffle(ISASpecInstruction):
    """
    Represents an irShuffle instruction with special latency properties.

    Properties:
        SpecialLatency: Indicates the first increment at which another irshuffle instruction
                        can be scheduled within `SpecialLatencyMax` latency.
        SpecialLatencyMax: Cannot enqueue any other irshuffle instruction within this latency
                           unless it is in `SpecialLatencyIncrement`.
        SpecialLatencyIncrement: Can only enqueue any other irshuffle instruction
                                 within `SpecialLatencyMax` only in increments of this value.
    """

    @classproperty
    def SpecialLatency(cls):
        """
        Special latency (indicates the first increment at which another irshuffle instruction
        can be scheduled within `SpecialLatencyMax` latency).

        Returns:
            int: The special latency increment.
        """
        return cls.SpecialLatencyIncrement

    @classproperty
    def SpecialLatencyMax(cls):
        """
        Special latency maximum (cannot enqueue any other irshuffle instruction within this latency
        unless it is in `SpecialLatencyIncrement`).

        Returns:
            int: The special latency maximum, which is 17.
        """
        return 17

    @classproperty
    def SpecialLatencyIncrement(cls):
        """
        Special latency increment (can only enqueue any other irshuffle instruction
        within `SpecialLatencyMax` only in increments of this value).

        Returns:
            int: The special latency increment, which is 5.
        """
        return 5

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 2.
        """
        return 2

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 23.
        """
        return 23

class Mac(ISASpecInstruction):
    """
    Represents a `mac` instruction.

    Element-wise polynomial multiplication and accumulation.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_mac.md
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
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 6.
        """
        return 6

class Maci(ISASpecInstruction):
    """
    Represents a `maci` instruction.

    Element-wise polynomial scaling by an immediate value and accumulation.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_maci.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class Move(ISASpecInstruction):
    """
    Represents a `move` instruction.

    This instruction copies data from one register to a different one.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_move.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class Mul(ISASpecInstruction):
    """
    Represents a `mul` instruction.

    This instructions performs element-wise polynomial multiplication.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_mul.md
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
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 6.
        """
        return 6

class Muli(ISASpecInstruction):
    """
    Represents a Muli instruction.

    This instruction performs element-wise polynomial scaling by an immediate value.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_muli.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class Nop(ISASpecInstruction):
    """
    Represents a `nop` instruction.

    This instruction adds a desired amount of idle cycles to the compute flow.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_nop.md
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

class NTT(ISASpecInstruction):
    """
    Represents an `ntt` instruction (Number Theoretic Transform).
    Converts positional form to NTT form.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_ntt.md
    """

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 2.
        """
        return 2

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 3.
        """
        return 3

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
            int: The latency, which is 6.
        """
        return 6

class rShuffle(ISASpecInstruction):
    """
    Represents an rShuffle instruction with special latency properties.

    Properties:
        SpecialLatency: Indicates the first increment at which another rshuffle instruction
                        can be scheduled within `SpecialLatencyMax` latency.
        SpecialLatencyMax: Cannot enqueue any other rshuffle instruction within this latency
                           unless it is in `SpecialLatencyIncrement`.
        SpecialLatencyIncrement: Can only enqueue any other rshuffle instruction
                                 within `SpecialLatencyMax` only in increments of this value.
    """

    @classproperty
    def SpecialLatency(cls):
        """
        Special latency (indicates the first increment at which another rshuffle instruction
        can be scheduled within `SpecialLatencyMax` latency).

        Returns:
            int: The special latency increment.
        """
        return cls.SpecialLatencyIncrement

    @classproperty
    def SpecialLatencyMax(cls):
        """
        Special latency maximum (cannot enqueue any other rshuffle instruction within this latency
        unless it is in `SpecialLatencyIncrement`).

        Returns:
            int: The special latency maximum, which is 17.
        """
        return 17

    @classproperty
    def SpecialLatencyIncrement(cls):
        """
        Special latency increment (can only enqueue any other rshuffle instruction
        within `SpecialLatencyMax` only in increments of this value).

        Returns:
            int: The special latency increment, which is 5.
        """
        return 5

    @classmethod
    def _get_numDests(cls) -> int:
        """
        Gets the number of destination operands.

        Returns:
            int: The number of destination operands, which is 2.
        """
        return 2

    @classmethod
    def _get_numSources(cls) -> int:
        """
        Gets the number of source operands.

        Returns:
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 23.
        """
        return 23

class Sub(ISASpecInstruction):
    """
    Represents a `sub` instruction.

    Element-wise polynomial subtraction.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_sub.md
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
            int: The number of source operands, which is 2.
        """
        return 2

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
            int: The latency, which is 6.
        """
        return 6

class twiNTT(ISASpecInstruction):
    """
    Represents a `twintt` instruction.

    This instruction performs on-die generation of twiddle factors for the next stage of iNTT.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_twintt.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class twNTT(ISASpecInstruction):
    """
    Represents a `twntt` instruction.

    This instruction performs on-die generation of twiddle factors for the next stage of NTT.

    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_twntt.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6

class xStore(ISASpecInstruction):
    """
    Represents an `xstore` instruction.

    This instruction transfers data from a register into the intermediate data buffer for subsequent transfer into SPAD.
    
    For more information, check the specification:
        https://github.com/IntelLabs/hec-assembler-tools/blob/master/docsrc/inst_spec/xinst/xinst_xstore.md
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
            int: The throughput, which is 1.
        """
        return 1

    @classmethod
    def _get_latency(cls) -> int:
        """
        Gets the latency of the instruction.

        Returns:
            int: The latency, which is 6.
        """
        return 6