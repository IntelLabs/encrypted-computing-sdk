# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing conversions or operations from isa to p-isa."""

from dataclasses import dataclass

from high_parser.pisa_operations import PIsaOp, Comment
from high_parser import KernelContext, Immediate, HighOp, Polys

from .basic import (
    Add,
    Sub,
    Muli,
    mixed_to_pisa_ops,
    split_last_rns_polys,
    duplicate_polys,
    common_immediates,
    muli_last_half,
    add_last_half,
    sub_last_half,
)
from .ntt import INTT, NTT


@dataclass
class Mod(HighOp):
    """Class representing mod down operation"""

    MOD_P = "_mod_p"
    MOD_QLAST = "_mod_qLast"

    context: KernelContext
    output: Polys
    input0: Polys
    var_suffix: str = MOD_QLAST  # default to qlast, use mod_p otherwise

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform an mod switch down"""
        # Immediates
        last_q = self.input0.rns - 1

        it = Immediate(name="it" + self.var_suffix + f"_{self.context.current_rns}")
        t = Immediate(name="t", rns=last_q)
        one, r2, iq = common_immediates(
            r2_rns=last_q,
            iq_rns=last_q,
            iq_suffix=self.var_suffix + f"_{self.context.current_rns}",
        )

        # Drop down input rns
        input_last_rns, input_remaining_rns = split_last_rns_polys(
            self.input0, self.context.current_rns
        )

        # Temp.
        temp_input_last_rns = duplicate_polys(input_last_rns, "y")
        temp_input_remaining_rns = duplicate_polys(input_remaining_rns, "x")

        # ckks variable
        p_half = Polys("pHalf", 1, rns=last_q)

        class Stage:
            """Stage hold a list of PISA ops, which are used by generate_mod_stages"""

            pisa_ops: list[PIsaOp]

            def __init__(self, pisa_ops: list[PIsaOp]):
                self.pisa_ops = pisa_ops

        def generate_mod_stages() -> list[Stage]:
            """Generate stages based on the current scheme (e.g. BGV or CKKS)"""
            # init empty stages
            stages = []
            if self.context.scheme == "BGV":
                stages.append(
                    Stage(
                        [
                            Comment("Mod Stage 0"),
                            Muli(
                                self.context,
                                temp_input_last_rns,
                                temp_input_last_rns,
                                it,
                            ),
                        ]
                    )
                )
                stages.append(
                    Stage(
                        [
                            Comment("Mod Stage 1"),
                            muli_last_half(
                                self.context,
                                temp_input_remaining_rns,
                                temp_input_last_rns,
                                r2,
                                input_remaining_rns,
                                last_q,
                            ),
                        ]
                    )
                )
                stages.append(
                    Stage(
                        [
                            Comment("Mod Stage 2"),
                            Muli(
                                self.context,
                                temp_input_remaining_rns,
                                temp_input_remaining_rns,
                                t,
                            ),
                            Comment("Add the delta correction to mod down polys"),
                            Add(
                                self.context,
                                temp_input_remaining_rns,
                                temp_input_remaining_rns,
                                input_remaining_rns,
                            ),
                        ]
                    )
                )
            elif self.context.scheme == "CKKS":
                # stage 1 is empty for CKKS
                stages.append(Stage([Comment("Mod Stage 0 - Empty")]))
                stages.append(
                    Stage(
                        [
                            Comment("Mod Stage 1 - add/sub half and muli"),
                            add_last_half(
                                self.context,
                                temp_input_last_rns,
                                temp_input_last_rns,
                                p_half,
                                Polys.from_polys(
                                    input_remaining_rns, mode="single_rns"
                                ),
                                last_q,
                            ),
                            sub_last_half(
                                self.context,
                                temp_input_remaining_rns,
                                temp_input_last_rns,
                                p_half,
                                input_remaining_rns,
                                last_q,
                            ),
                            Muli(
                                self.context,
                                temp_input_remaining_rns,
                                temp_input_remaining_rns,
                                r2,
                            ),
                        ]
                    )
                )
                stages.append(
                    Stage(
                        [
                            Comment("Mod Stage 2 - Sub"),
                            Sub(
                                self.context,
                                temp_input_remaining_rns,
                                input_remaining_rns,
                                temp_input_remaining_rns,
                            ),
                        ]
                    )
                )

            return stages

        stages = generate_mod_stages()

        # Compute the `delta_i = t * [-t^-1 * c_i] mod ql` where `i` are the parts
        # The `one` acts as a select flag as whether or not R2 the Montgomery
        # factor should be applied
        return mixed_to_pisa_ops(
            [
                Comment("Start of mod kernel"),
                Comment("Compute the delta from last rns"),
                INTT(self.context, temp_input_last_rns, input_last_rns),
            ]
            + stages[0].pisa_ops
            + [
                Muli(self.context, temp_input_last_rns, temp_input_last_rns, one),
                Comment("Compute the remaining rns"),
            ]
            + stages[1].pisa_ops
            + [
                NTT(self.context, temp_input_remaining_rns, temp_input_remaining_rns),
            ]
            + stages[2].pisa_ops
            + [
                Muli(self.context, self.output, temp_input_remaining_rns, iq),
                Comment("End of mod kernel"),
            ]
        )


@dataclass
class ModUp(HighOp):
    """Class representing mod switch up operation"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform a modulus switch up (modup)"""

        one = Immediate(name="one")
        r_squared = Immediate(name="R2", rns=self.output.rns)

        # extended_poly like input_last_part will have only the last `part`
        extended_poly = Polys.from_polys(self.input0)
        extended_poly.name = "ct"

        return mixed_to_pisa_ops(
            [
                Comment("Start of modup kernel"),
                INTT(self.context, extended_poly, self.input0),
                Comment("Multiply Montgomery"),
                Muli(self.context, self.output, extended_poly, one),
                Muli(self.context, self.output, self.output, r_squared),
                Comment("Transform back to residue domain"),
                NTT(self.context, self.output, self.output),
                Comment("End of modup kernel"),
            ]
        )
