# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing implementation for rotate kernel."""

from dataclasses import dataclass

from high_parser.pisa_operations import PIsaOp, Comment
from high_parser import KernelContext, HighOp, Polys, KeyPolys

from .basic import Add, KeyMul, mixed_to_pisa_ops, extract_last_part_polys
from .decomp import DigitDecompExtend
from .mod import Mod
from .ntt import INTT, NTT


@dataclass
class Rotate(HighOp):
    """Class representing rotate operation"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform a rotate. Note:
        currently only supports polynomials with two parts. Currently only
        supports number of digits equal to the RNS size"""
        self.output.parts = 2
        self.input0.parts = 2

        relin_key = KeyPolys(
            "gk", parts=2, rns=self.context.key_rns, digits=self.input0.rns
        )
        mul_by_rlk = Polys("c2_gk", parts=2, rns=self.context.key_rns)
        mul_by_rlk_modded_down = Polys.from_polys(mul_by_rlk)
        mul_by_rlk_modded_down.rns = self.input0.rns
        mul_by_rlk_modded_down.name = self.output.name

        input_last_part, last_coeff, upto_last_coeffs = extract_last_part_polys(
            self.input0, self.context.key_rns
        )

        cd = Polys.from_polys(self.input0)
        cd.name = "cd"
        cd.parts = 1
        cd.start_parts = 0

        start_input = Polys.from_polys(self.input0)
        start_input.parts = 1
        start_input.start_parts = 0

        first_part_rlk = Polys.from_polys(mul_by_rlk_modded_down)
        first_part_rlk.parts = 1
        first_part_rlk.start_parts = 0

        return mixed_to_pisa_ops(
            Comment("Start of rotate kernel"),
            Comment("Digit Decomp"),
            DigitDecompExtend(self.context, last_coeff, input_last_part),
            Comment("Multiply by rotate key"),
            KeyMul(self.context, mul_by_rlk, upto_last_coeffs, relin_key, 1),
            Comment("Mod switch down to Q"),
            Mod(self.context, mul_by_rlk_modded_down, mul_by_rlk, Mod.MOD_P),
            INTT(self.context, cd, start_input),
            NTT(self.context, cd, cd),
            Add(self.context, self.output, cd, first_part_rlk),
            Comment("End of rotate kernel"),
        )
