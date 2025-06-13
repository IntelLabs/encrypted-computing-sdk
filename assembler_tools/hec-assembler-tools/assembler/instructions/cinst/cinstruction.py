# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""CInstruction base class for C-instructions in the assembler."""

from typing import List, Any
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

    def __init__(
        self, instruction_id: int, throughput: int, latency: int, comment: str = ""
    ):
        """
        Constructs a new CInstruction.

        Parameters:
            instruction_id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            throughput (int): The throughput of the instruction.
            latency (int): The latency of the instruction.
            comment (str, optional): An optional comment for the instruction.
        """
        super().__init__(instruction_id, throughput, latency, comment=comment)

    @classmethod
    def _get_op_name_asm(cls) -> str:
        """
        Returns the ASM name for the operation.

        This method must be implemented by derived CInstruction classes.

        Returns:
            str: The ASM name for the operation.
        """
        raise NotImplementedError(
            "Derived CInstruction must implement _get_op_name_asm."
        )

    # Methods and properties
    # ----------------------

    def _get_cycle_ready(self):
        """
        Returns the cycle ready value for the instruction.

        This method overrides the base method to provide a specific cycle ready value for CInstructions.

        Returns:
            CycleType: A CycleType object with bundle and cycle set to 0.
        """
        return CycleType(bundle=0, cycle=0)

    def _to_casmisa_format(self, *extra_args) -> str:
        """
        Converts the instruction to CInst ASM-ISA format.

        This method constructs the ASM-ISA format string for the instruction by combining
        the instruction's sources and destinations with any additional arguments.

        Parameters:
            extra_args: Additional arguments for the conversion.

        Returns:
            str: The CInst ASM-ISA format string of the instruction.
        """

        preamble: List[Any] = []
        # instruction sources
        extra_args = tuple(src.to_casmisa_format() for src in self.sources) + extra_args
        # instruction destinations
        extra_args = tuple(dst.to_casmisa_format() for dst in self.dests) + extra_args
        return self.to_string_format(preamble, self.op_name_asm, *extra_args)
