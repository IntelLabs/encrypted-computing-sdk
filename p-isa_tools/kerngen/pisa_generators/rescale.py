# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright (C) 2024 Intel Corporation

"""Module containing conversions or operations from isa to p-isa."""

from dataclasses import dataclass

from high_parser.pisa_operations import PIsaOp, Comment

from high_parser import KernelContext, HighOp, Polys

from .basic import (
    Muli,
    mixed_to_pisa_ops,
    Sub,
    split_last_rns_polys,
    duplicate_polys,
    common_immediates,
    add_last_half,
    sub_last_half,
)
from .ntt import INTT, NTT


@dataclass
class Rescale(HighOp):
    """Class representing mod down operation"""

    MOD_QLAST = "_mod_qLast"
    context: KernelContext
    output: Polys
    input0: Polys
    var_suffix: str = MOD_QLAST  # default to qlast

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform an mod switch down"""

        # Immediates
        last_q = self.input0.rns - 1

        one, r2, iq = common_immediates(
            r2_rns=last_q,
            iq_rns=last_q,
            iq_suffix=self.var_suffix + f"_{self.context.current_rns}"
        )

        q_last_half = Polys("qLastHalf", 1, self.input0.rns)
        q_i_last_half = Polys(
            "qiLastHalf" + f"_{self.context.current_rns}", 1, rns=last_q
        )

        # split input
        input_last_rns, input_remaining_rns = split_last_rns_polys(
            self.input0, self.context.current_rns
        )

        # Create temp vars for input_last/remaining
        temp_input_last_rns = duplicate_polys(input_last_rns, "y")
        temp_input_remaining_rns = duplicate_polys(input_remaining_rns, "x")

        # Compute the `delta_i = t * [-t^-1 * c_i] mod ql` where `i` are the parts
        # The `one` acts as a select flag as whether or not R2 the Montgomery
        # factor should be applied
        return mixed_to_pisa_ops(
            [
                Comment("Start of Rescale kernel."),
                INTT(self.context, temp_input_last_rns, input_last_rns),
                Muli(self.context, temp_input_last_rns, temp_input_last_rns, one),
                Comment("Add the last part of the input to y"),
                add_last_half(
                    self.context,
                    temp_input_last_rns,
                    temp_input_last_rns,
                    q_last_half,
                    Polys.from_polys(input_remaining_rns, mode="single_rns"),
                    last_q,
                ),
                Comment("Subtract q_i (last half/last rns) from y"),
                sub_last_half(
                    self.context,
                    temp_input_remaining_rns,
                    temp_input_last_rns,
                    q_i_last_half,
                    input_remaining_rns,
                    last_q,
                ),
                Muli(
                    self.context, temp_input_remaining_rns, temp_input_remaining_rns, r2
                ),
                NTT(self.context, temp_input_remaining_rns, temp_input_remaining_rns),
                Sub(
                    self.context,
                    temp_input_remaining_rns,
                    Polys.from_polys(self.input0, mode="drop_last_rns"),
                    temp_input_remaining_rns,
                ),
                Muli(self.context, self.output, temp_input_remaining_rns, iq),
                Comment("End of Rescale kernel."),
            ]
        )
