# Copyright (C) 2024 Intel Corporation

"""Module containing conversions or operations from isa to p-isa."""

from dataclasses import dataclass

from high_parser.pisa_operations import PIsaOp
from high_parser.parser import Context
from high_parser.highop import HighOp
from high_parser.polys import Polys

from .basic import Copy, Mul


@dataclass
class Square(HighOp):
    """Class representing the high-level squaring operation"""

    context: Context
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa equivalent of an Add"""
        intermediate = Polys(name="inter", parts=self.input0.parts, rns=self.input0.rns)

        copy = Copy(self.context, intermediate, self.input0)
        mul = Mul(self.context, self.output, intermediate, self.input0)

        return [*copy.to_pisa(), *mul.to_pisa()]
