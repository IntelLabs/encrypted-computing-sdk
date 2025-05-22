# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing relin."""
from dataclasses import dataclass
from high_parser.pisa_operations import PIsaOp, Comment
from high_parser import KernelContext, HighOp, KeyPolys, Polys
from .basic import Add, KeyMul, mixed_to_pisa_ops, extract_last_part_polys

from .mod import Mod
from .decomp import DigitDecompExtend


@dataclass
class Relin(HighOp):
    """Class representing relinearization operation"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform a relinearization (relin). Note:
        currently only supports polynomials with two parts. Currently only
        supports number of digits equal to the RNS size"""
        self.output.parts = 2
        self.input0.parts = 3
        relin_key = KeyPolys(
            "rlk", parts=2, rns=self.context.key_rns, digits=self.input0.rns
        )

        mul_by_rlk = Polys("c2_rlk", parts=2, rns=self.context.key_rns)

        mul_by_rlk_modded_down = Polys.from_polys(mul_by_rlk)
        mul_by_rlk_modded_down.rns = self.input0.rns

        input_last_part, last_coeff, upto_last_coeffs = extract_last_part_polys(
            self.input0, self.context.key_rns
        )

        add_original = Polys.from_polys(mul_by_rlk_modded_down)
        add_original.name = self.input0.name
        return mixed_to_pisa_ops(
            Comment("Start of relin kernel"),
            Comment("Digit decomposition and extend base from Q to PQ"),
            DigitDecompExtend(self.context, last_coeff, input_last_part),
            Comment("Multiply by relin key"),
            KeyMul(self.context, mul_by_rlk, upto_last_coeffs, relin_key, 2),
            Comment("Mod switch down to Q"),
            Mod(self.context, mul_by_rlk_modded_down, mul_by_rlk, Mod.MOD_P),
            Comment("Add to original poly"),
            Add(self.context, self.output, mul_by_rlk_modded_down, add_original),
            Comment("End of relin kernel"),
        )
