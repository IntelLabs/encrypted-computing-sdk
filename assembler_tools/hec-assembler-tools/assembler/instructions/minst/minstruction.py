# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from assembler.common.cycle_tracking import CycleType
from ..instruction import BaseInstruction


class MInstruction(BaseInstruction):
    """
    Represents a memory-level instruction (MInstruction).

    This class is used to encapsulate the properties and behaviors of a memory-level instruction,
    including its throughput, latency, and a unique counter value that increases with each
    MInstruction created.

    Methods:
        count: Returns the MInstruction counter value for this instruction.
    """

    __minst_count = 0  # Internal Minst counter

    def __init__(self, id: int, throughput: int, latency: int, comment: str = ""):
        """
        Constructs a new MInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            throughput (int): The throughput of the instruction.

            latency (int): The latency of the instruction.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        super().__init__(id, throughput, latency, comment=comment)
        self.__count = MInstruction.__minst_count

    @property
    def count(self):
        """
        Returns the MInstruction counter value for this instruction.

        This value monotonically increases per MInstruction created.

        Returns:
            int: The counter value for this MInstruction.
        """
        return self.__count

    def _get_cycle_ready(self):
        """
        Returns a CycleType object indicating when the instruction is ready.

        Returns:
            CycleType: A CycleType object with bundle and cycle set to 0.
        """
        return CycleType(bundle=0, cycle=0)

    def _to_masmisa_format(self, *extra_args) -> str:
        """
        Converts the instruction to MInst ASM-ISA format.

        See inherited for more information.

        Parameters:
            extra_args: Additional arguments for formatting.

        Returns:
            str: The instruction in MInst ASM-ISA format.
        """
        # Instruction sources
        extra_args = tuple(src.to_masmisa_format() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.to_masmisa_format() for dst in self.dests) + extra_args
        return self.to_string_format(None, self.op_name_asm, *extra_args)
