# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing conversions or operations from isa to p-isa."""

from dataclasses import dataclass
import itertools as it

import high_parser.pisa_operations as pisa_op
from high_parser.pisa_operations import PIsaOp
from high_parser import KernelContext, Immediate, HighOp, Polys

from .basic import Mul, Muli, mixed_to_pisa_ops


def generate_unit_index(size: int, op: pisa_op.NTT | pisa_op.INTT):
    """Helper to return unit indices for ntt/intt"""
    for i in range(int(size / 2)):
        if issubclass(op, pisa_op.NTT):
            yield (i, int(size / 2) + i, i * 2, i * 2 + 1)
        else:
            yield (i * 2, i * 2 + 1, i, int(size / 2) + i)


# pylint: disable=too-many-arguments
def butterflies_ops(
    op: pisa_op.NTT | pisa_op.INTT,
    context: KernelContext,
    output: Polys,
    outtmp: Polys,
    input0: Polys,
    *,  # only kwargs after
    init_input: bool = False,
    unit_size: int = 8192
) -> list[PIsaOp]:
    """Helper to return butterflies pisa operations for NTT/INTT"""
    ntt_stages_div_by_two = context.ntt_stages % 2

    # generate the stages, which depends on the total ntt stages.
    stage_dst_srcs = [
        (
            (stage, outtmp, output)
            if ntt_stages_div_by_two == stage % 2
            else (stage, output, outtmp)
        )
        for stage in range(context.ntt_stages)
    ]

    # For INTTs, start with input0 on the first stage destinations
    if init_input is True:
        stage_dst_srcs[0] = (
            (0, outtmp, input0) if ntt_stages_div_by_two == 0 else (0, output, input0)
        )

    return [
        op(
            context.label,
            dst(part, q, unit[0]),
            dst(part, q, unit[1]),
            src(part, q, unit[2]),
            src(part, q, unit[3]),
            stage,
            unit[0] if issubclass(op, pisa_op.NTT) else unit[2],
            q,
        )
        # units for omegas (aka w) taken from 16K onwards
        for part, (stage, dst, src), q, unit in it.product(
            range(input0.start_parts, input0.parts),
            stage_dst_srcs,
            range(input0.start_rns, input0.rns),
            generate_unit_index(int(context.poly_order / unit_size), op),
        )
    ]


@dataclass
class NTT(HighOp):
    """Class representing the NTT"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform an NTT"""
        # TODO Is this passed in?
        psi = Polys(
            "psi", parts=1, rns=self.input0.rns, start_rns=self.input0.start_rns
        )
        # TODO We need to decide whether output symbols need to be defined
        outtmp = Polys("outtmp", self.output.parts, self.output.rns)

        # Essentially a scalar mul since psi 1 part
        if self.context.ntt_stages % 2 == 0:
            # Even case: butterfly input starts "coeff"
            mul = Mul(self.context, self.output, self.input0, psi)
        else:
            # Odd case: butterfly input stats with "outtmp"
            mul = Mul(self.context, outtmp, self.input0, psi)

        butterflies = butterflies_ops(
            pisa_op.NTT,
            context=self.context,
            output=self.output,
            outtmp=outtmp,
            input0=self.input0,
        )

        return mixed_to_pisa_ops(mul, butterflies)


@dataclass
class INTT(HighOp):
    """Class representing the INTT"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform an INTT"""
        # TODO Is this passed in?
        ipsi = Polys(
            "ipsi", parts=1, rns=self.input0.rns, start_rns=self.input0.start_rns
        )
        # TODO We need to decide whether output symbols need to be defined
        outtmp = Polys("outtmp", self.output.parts, self.output.rns)
        iN = Immediate(name="iN")

        butterflies = butterflies_ops(
            pisa_op.INTT,
            context=self.context,
            output=self.output,
            outtmp=outtmp,
            input0=self.input0,
            init_input=True,
        )

        # Essentially a scalar mul since ipsi 1 part
        mul = Mul(self.context, self.output, self.output, ipsi)
        muli = Muli(self.context, self.output, self.output, iN)

        return mixed_to_pisa_ops(butterflies, mul, muli)
