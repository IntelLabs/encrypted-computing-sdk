# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""Module containing digit decomposition/base extend"""

from string import ascii_letters
import itertools as it

from dataclasses import dataclass
import high_parser.pisa_operations as pisa_op
from high_parser.pisa_operations import PIsaOp
from high_parser import KernelContext, HighOp, Immediate, Polys

from .basic import Muli, mixed_to_pisa_ops
from .ntt import INTT, NTT


@dataclass
class DigitDecompExtend(HighOp):
    """Class representing Digit decomposition and base extension"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code performing Digit decomposition followed by
        base extension"""

        rns_poly = Polys.from_polys(self.input0)
        rns_poly.name = "ct"

        one = Immediate(name="one")
        r2 = Immediate(name="R2", rns=self.context.key_rns)

        ls: list[pisa_op] = []
        for input_rns_index in range(self.input0.start_rns, self.input0.rns):
            # muli for 0-current_rns
            ls.extend(
                pisa_op.Muli(
                    self.context.label,
                    self.output(part, pq, unit),
                    rns_poly(part, input_rns_index, unit),
                    r2(part, pq, unit),
                    pq,
                )
                for part, pq, unit in it.product(
                    range(self.input0.start_parts, self.input0.parts),
                    range(self.context.current_rns),
                    range(self.context.units),
                )
            )
            # muli for krns
            ls.extend(
                pisa_op.Muli(
                    self.context.label,
                    self.output(part, pq, unit),
                    rns_poly(part, input_rns_index, unit),
                    r2(part, pq, unit),
                    pq,
                )
                for part, pq, unit in it.product(
                    range(self.input0.start_parts, self.input0.parts),
                    range(self.context.max_rns, self.context.key_rns),
                    range(self.context.units),
                )
            )

            output_tmp = Polys.from_polys(self.output)
            output_tmp.name += "_" + ascii_letters[input_rns_index]
            output_split = Polys.from_polys(self.output)
            output_split.rns = self.context.current_rns
            # ntt for 0-current_rns
            ls.extend(NTT(self.context, output_tmp, output_split).to_pisa())

            output_split = Polys.from_polys(self.output)
            output_split.rns = self.context.key_rns
            output_split.start_rns = self.context.max_rns
            # ntt for krns
            ls.extend(NTT(self.context, output_tmp, output_split).to_pisa())

        return mixed_to_pisa_ops(
            INTT(self.context, rns_poly, self.input0),
            Muli(self.context, rns_poly, rns_poly, one),
            ls,
        )
