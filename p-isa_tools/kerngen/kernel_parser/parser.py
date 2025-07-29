# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""Module for parsing kernel commands from Kerngen"""

import re

from high_parser.types import Context, Immediate, KernelContext, Polys
from pisa_generators.basic import Add, Copy, HighOp, Mul, Muli, Sub
from pisa_generators.mod import Mod, ModUp
from pisa_generators.ntt import INTT, NTT
from pisa_generators.relin import Relin
from pisa_generators.rescale import Rescale
from pisa_generators.rotate import Rotate
from pisa_generators.square import Square


class KernelParser:
    """Parser for kernel operations."""

    high_op_map = {
        "Add": Add,
        "Mul": Mul,
        "Muli": Muli,
        "Copy": Copy,
        "Sub": Sub,
        "Square": Square,
        "NTT": NTT,
        "INTT": INTT,
        "Mod": Mod,
        "ModUp": ModUp,
        "Relin": Relin,
        "Rotate": Rotate,
        "Rescale": Rescale,
    }

    @staticmethod
    def parse_context(context_str: str) -> KernelContext:
        """Parse the context string and return a KernelContext object."""
        context_match = re.search(
            r"KernelContext\(scheme='(?P<scheme>\w+)', " + r"poly_order=(?P<poly_order>\w+), key_rns=(?P<key_rns>\w+), "
            r"current_rns=(?P<current_rns>\w+), .*? label='(?P<label>\w+)'\)",
            context_str,
        )
        if not context_match:
            raise ValueError("Invalid context string format.")
        return KernelContext.from_context(
            Context(
                scheme=context_match.group("scheme"),
                poly_order=int(context_match.group("poly_order")),
                key_rns=int(context_match.group("key_rns")),
                current_rns=int(context_match.group("current_rns")),
                max_rns=int(context_match.group("key_rns")) - 1,
            ),
            label=str(context_match.group("label")),
        )

    @staticmethod
    def parse_polys(polys_str: str) -> Polys:
        """Parse the Polys string and return a Polys object."""
        polys_match = re.search(r"Polys\(name=(.*?), parts=(\d+), rns=(\d+)\)", polys_str)
        if not polys_match:
            raise ValueError("Invalid Polys string format.")
        name, parts, rns = polys_match.groups()
        return Polys(name=name, parts=int(parts), rns=int(rns))

    @staticmethod
    def parse_immediate(immediate_str: str) -> Immediate:
        """Parse the Immediate string and return an Immediate object."""
        immediate_match = re.search(r"Immediate\(name='(?P<name>\w+)', rns=(?P<rns>\w+)\)", immediate_str)
        if not immediate_match:
            raise ValueError("Invalid Immediate string format.")
        name, rns = immediate_match.group("name"), immediate_match.group("rns")
        rns = None if rns == "None" else int(rns)
        return Immediate(name=name, rns=rns)

    @staticmethod
    def parse_high_op(kernel_str: str) -> HighOp:
        """Parse a HighOp kernel string and return the corresponding object."""
        pattern = r"### Kernel \(\d+\): (?P<op_type>\w+)\(context=(KernelContext\(.*?\)), " r"output=(Polys\(.*?\)), input0=(Polys\(.*?\))"
        has_second_input = False
        # Check if the kernel string contains "input1" or not
        if "input1" not in kernel_str:
            # Match the operation type and its arguments
            high_op_match = re.search(pattern, kernel_str)
        else:
            # Adjust the pattern to include input1
            pattern += r", input1=(Polys\(.*?\)\)|Immediate\(.*?\)\))"
            # Match the operation type and its arguments
            high_op_match = re.search(pattern, kernel_str)
            has_second_input = True

        if not high_op_match:
            raise ValueError(f"Invalid kernel string format: {kernel_str}.")

        op_type = high_op_match.group("op_type")
        context_str, output_str, input0_str = high_op_match.groups()[1:4]

        if has_second_input:
            input1_str = high_op_match.group(5)

        # Parse the components
        context = KernelParser.parse_context(context_str)
        output = KernelParser.parse_polys(output_str)
        input0 = KernelParser.parse_polys(input0_str)
        if has_second_input:
            if op_type == "Muli":
                input1 = KernelParser.parse_immediate(input1_str)
            else:
                # For other operations, parse as Polys
                input1 = KernelParser.parse_polys(input1_str)

        if op_type not in KernelParser.high_op_map:
            raise ValueError(f"Unsupported HighOp type: {op_type}")

        # Instantiate the HighOp object
        if has_second_input:
            return KernelParser.high_op_map[op_type](context=context, output=output, input0=input0, input1=input1)
        # For operations without a second input, we can ignore the input1 parameter
        return KernelParser.high_op_map[op_type](context=context, output=output, input0=input0)

    @staticmethod
    def parse_kernel(kernel_str: str) -> HighOp:
        """Parse a kernel string and return the corresponding HighOp object."""
        return KernelParser.parse_high_op(kernel_str)
