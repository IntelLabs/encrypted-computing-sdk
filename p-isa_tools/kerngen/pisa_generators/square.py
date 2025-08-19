# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing conversions or operations from isa to p-isa."""

from dataclasses import dataclass

from high_parser import Context, HighOp, Polys
from high_parser.pisa_operations import PIsaOp

from .basic import Copy, Mul, mixed_to_pisa_ops


@dataclass
class Square(HighOp):
    """Class representing the high-level squaring operation"""

    context: Context
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa equivalent of an Add"""
        intermediate = Polys(name="inter", parts=self.input0.parts, rns=self.input0.rns)

        return mixed_to_pisa_ops(
            Copy(self.context, intermediate, self.input0),
            Mul(self.context, self.output, intermediate, self.input0),
        )
