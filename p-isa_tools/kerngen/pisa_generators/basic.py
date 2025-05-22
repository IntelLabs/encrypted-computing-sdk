# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module containing conversions or operations from isa to p-isa."""

import itertools as it
from dataclasses import dataclass
from typing import ClassVar, Iterable, Tuple
from string import ascii_letters

import high_parser.pisa_operations as pisa_op
from high_parser.pisa_operations import PIsaOp
from high_parser import (
    Immediate,
    HighOp,
    expand_ios,
    Polys,
    KeyPolys,
    KernelContext,
)


# TODO move this to kernel utils
def mixed_to_pisa_ops(*args) -> list[PIsaOp]:
    """Transform mixed list of op types to PIsaOp only"""
    if len(args) == 1:
        return _mixed_to_pisa_ops(*args)
    return _mixed_to_pisa_ops(args)


def _mixed_to_pisa_ops(ops: Iterable[PIsaOp | list[PIsaOp] | HighOp]) -> list[PIsaOp]:
    """Helper to process mixed list of op types to PIsaOp only"""

    def helper(op) -> list[PIsaOp]:
        if isinstance(op, PIsaOp):
            return [op]
        if isinstance(op, list):
            if not all(isinstance(elem, PIsaOp) for elem in op):
                raise ValueError("Not all elements in list are pisa ops")
            return op
        return op.to_pisa()

    ops_pisa_clusters: Iterable[list[PIsaOp | HighOp]] = map(helper, ops)
    # Flattens the list returned
    return [pisa_op for pisa_ops in ops_pisa_clusters for pisa_op in pisa_ops]


@dataclass
class CartesianOp(HighOp):
    """Class representing the high-level cartesian operation"""

    context: KernelContext
    output: Polys
    input0: Polys
    input1: Polys

    # class vars are not included in __init__
    op: ClassVar[PIsaOp]

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa equivalent of an Add"""
        if self.input0.parts == self.input1.parts:
            return [
                self.op(self.context.label, *expand_io, rns)
                for expand_io, rns in expand_ios(
                    self.context, self.output, self.input0, self.input1
                )
            ]

        # Not the same number of parts
        first, second = (
            (self.input0, self.input1)
            if self.input0.parts < self.input1.parts
            else (self.input1, self.input0)
        )

        ls: list[PIsaOp] = []
        for unit, q in it.product(
            range(self.context.units), range(self.input0.start_rns, self.input0.rns)
        ):
            ls.extend(
                self.op(
                    self.context.label,
                    self.output(part, q, unit),
                    first(part, q, unit),
                    second(0, q, unit),
                    q,
                )
                for part in range(first.parts)
            )
            ls.extend(
                pisa_op.Copy(
                    self.context.label,
                    self.output(part, q, unit),
                    second(part, q, unit),
                )
                for part in range(first.parts, second.parts)
            )
        return ls


class Add(CartesianOp):
    """Class representing the high-level addition operation"""

    op = pisa_op.Add


class Sub(CartesianOp):
    """Class representing the high-level subtraction operation"""

    op = pisa_op.Sub


InIdxs = list[tuple[int, int]]


def convolution_indices(input0: Polys, input1: Polys) -> list[InIdxs]:
    """Helper gives convolution of parts indices"""
    # start_* is the deg + 1 of a polynomial (the vector)
    idxs: list[InIdxs] = [[] for _ in range(input0.parts + input1.parts - 1)]
    for t in it.product(
        range(input0.start_parts, input0.parts), range(input1.start_parts, input1.parts)
    ):
        idxs[sum(t)].append(t)
    return idxs


@dataclass
class Mul(HighOp):
    """Class representing the high-level multiplication operation"""

    context: KernelContext
    output: Polys
    input0: Polys
    input1: KeyPolys | Polys

    # pylint: disable=too-many-arguments
    def generate_unit(
        self,
        unit: int,
        q: int,
        out_idx: int,
        in_idxs: InIdxs,
        *,
        digit: int | None = None
    ):
        """Helper for a given unit and q generate the p-isa ops for a multiplication"""

        def get_pisa_op(num):
            yield pisa_op.Mul
            yield from (pisa_op.Mac for op in range(num - 1))

        return [
            op(
                self.context.label,
                self.output(out_idx, q, unit),
                self.input0(in0_idx, q, unit),
                (
                    self.input1(in1_idx, q, unit)
                    if digit is None
                    else self.input1(digit, in1_idx, q, unit)
                ),
                q,
            )
            for (in0_idx, in1_idx), op in zip(in_idxs, get_pisa_op(len(in_idxs)))
        ]

    def _keypolys_to_pisa(self, all_idxs: list[InIdxs]) -> list[PIsaOp]:
        ls = []
        for digit, unit, q in it.product(
            range(self.input1.digits),  # NOTE digits from input1 NOT input0
            range(self.context.units),
            range(self.input0.start_rns, self.input0.rns),
        ):
            for out_idx, in_idxs in enumerate(all_idxs):
                ls.extend(self.generate_unit(unit, q, out_idx, in_idxs, digit=digit))

        return ls

    def _polys_to_pisa(self, all_idxs: list[InIdxs]) -> list[PIsaOp]:
        ls = []
        for unit, q in it.product(
            range(self.context.units), range(self.input0.start_rns, self.input0.rns)
        ):
            for out_idx, in_idxs in enumerate(all_idxs):
                ls.extend(self.generate_unit(unit, q, out_idx, in_idxs))

        return ls

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa  equivalent of a Mul"""

        all_idxs: list[InIdxs] = convolution_indices(self.input0, self.input1)
        if isinstance(self.input1, KeyPolys):
            return self._keypolys_to_pisa(all_idxs)
        return self._polys_to_pisa(all_idxs)


@dataclass
class Muli(HighOp):
    """Class representing the high-level multiplication operation"""

    context: KernelContext
    output: Polys
    input0: Polys
    input1: Immediate

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa equivalent of a multiply by an immediate. Note that
        since immediates have one part this is a scalar multiplication."""

        # Parts is last for convention of units, rns, parts
        return [
            pisa_op.Muli(
                self.context.label,
                self.output(part, q, unit),
                self.input0(part, q, unit),
                self.input1(part, q, unit),
                q,
            )
            for unit, q, part in it.product(
                range(self.context.units),
                range(self.input0.start_rns, self.input0.rns),
                range(self.input0.start_parts, self.input0.parts),
            )
        ]


@dataclass
class Copy(HighOp):
    """Class representing the high-level copy operation"""

    context: KernelContext
    output: Polys
    input0: Polys

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa equivalent of a Copy"""
        return [
            pisa_op.Copy(self.context.label, *expand_io)
            for expand_io, _ in expand_ios(self.context, self.output, self.input0)
        ]


@dataclass
class KeyMul(HighOp):
    """Class representing a key multiplication operation"""

    context: KernelContext
    output: Polys
    input0: Polys
    input1: KeyPolys
    input0_fixed_part: int

    def to_pisa(self) -> list[PIsaOp]:
        """Return the p-isa code to perform a key multiplication"""

        def get_pisa_op(num):
            yield 0, pisa_op.Mul
            yield from ((op, pisa_op.Mac) for op in range(1, num))

        ls: list[pisa_op] = []
        for digit, op in get_pisa_op(self.input1.digits):
            input0_tmp = Polys.from_polys(self.input0)
            input0_tmp.name += "_" + ascii_letters[digit]

            # mul/mac for 0-current_rns
            ls.extend(
                op(
                    self.context.label,
                    self.output(part, q, unit),
                    input0_tmp(self.input0_fixed_part, q, unit),
                    self.input1(digit, part, q, unit),
                    q,
                )
                for part, q, unit in it.product(
                    range(self.input1.start_parts, self.input1.parts),
                    range(self.context.current_rns),
                    range(self.context.units),
                )
            )
            # mul/mac for max_rns-krns terms
            ls.extend(
                op(
                    self.context.label,
                    self.output(part, q, unit),
                    input0_tmp(self.input0_fixed_part, q, unit),
                    self.input1(digit, part, q, unit),
                    q,
                )
                for part, q, unit in it.product(
                    range(self.input1.start_parts, self.input1.parts),
                    range(self.context.max_rns, self.context.key_rns),
                    range(self.context.units),
                )
            )
        return ls


def extract_last_part_polys(input0: Polys, rns: int) -> Tuple[Polys, Polys, Polys]:
    """Split and extract the last part of input0 with a change of rns"""
    input_last_part = Polys.from_polys(input0, mode="last_part")
    input_last_part.name = input0.name

    last_coeff = Polys.from_polys(input_last_part)
    last_coeff.name = "coeffs"
    last_coeff.rns = rns

    upto_last_coeffs = Polys.from_polys(last_coeff)
    upto_last_coeffs.parts = 1
    upto_last_coeffs.start_parts = 0

    return input_last_part, last_coeff, upto_last_coeffs


def split_last_rns_polys(input0: Polys, current_rns) -> Tuple[Polys, Polys]:
    """Split and extract last RNS of input0"""
    if input0.rns <= current_rns:
        return Polys.from_polys(input0, mode="last_rns"), Polys.from_polys(
            input0, mode="drop_last_rns"
        )

    # do not include consumed rns
    remaining = Polys.from_polys(input0)
    remaining.rns = current_rns
    return Polys.from_polys(input0, mode="last_rns"), remaining


def duplicate_polys(input0: Polys, name: str) -> Polys:
    """Creates a duplicate of input0 with new name"""
    return Polys(name, input0.parts, input0.rns, input0.start_parts, input0.start_rns)


def common_immediates(
    r2_rns=None, iq_rns=None, iq_suffix=""
) -> Tuple[Immediate, Immediate, Immediate]:
    """Generate commonly used immediates"""
    return (
        Immediate(name="one"),
        Immediate(name="R2", rns=r2_rns),
        Immediate(name="iq" + iq_suffix, rns=iq_rns),
    )


# pylint: disable=too-many-arguments
# pylint: disable=too-many-positional-arguments


@dataclass
class PartialOpOptions:
    """Optional arguments for partial_op helper function"""

    output_last_q: bool = False
    input0_last_q: bool = False
    input1_last_q: bool = False
    input1_first_part: bool = False
    op_last_q: bool = False


@dataclass
class PartialOpPolys:
    """Polynomials used in partial ops"""

    output: Polys
    input0: Polys
    input1: Polys
    input_remaining_rns: Polys


def partial_op(
    context: KernelContext,
    op,
    polys: PartialOpPolys,
    options: PartialOpOptions,
    last_q: int,
):
    """ "A helper function to perform partial operation, such as add/sub on last half (input1) to all of input0"""

    return [
        op(
            context.label,
            polys.output(part, last_q if options.output_last_q else q, unit),
            polys.input0(part, last_q if options.input0_last_q else q, unit),
            polys.input1(
                0 if options.input1_first_part else part,
                last_q if options.input1_last_q else q,
                unit,
            ),
            last_q if options.op_last_q else q,
        )
        for part, q, unit in it.product(
            range(polys.input_remaining_rns.parts),
            range(polys.input_remaining_rns.start_rns, polys.input_remaining_rns.rns),
            range(context.units),
        )
    ]


def add_last_half(
    context: KernelContext,
    output: Polys,
    input0: Polys,
    input1: Polys,
    input_remaining_rns: Polys,
    last_q: int,
):
    """Add input0 to input1 (first part)"""
    return partial_op(
        context,
        pisa_op.Add,
        PartialOpPolys(output, input0, input1, input_remaining_rns),
        PartialOpOptions(
            output_last_q=True,
            input0_last_q=True,
            input1_last_q=True,
            input1_first_part=True,
            op_last_q=True,
        ),
        last_q,
    )


def sub_last_half(
    context: KernelContext,
    output: Polys,
    input0: Polys,
    input1: Polys,
    input_remaining_rns: Polys,
    last_q: int,
):
    """Subtract input1 (first part) with input0 (last RNS)"""
    return partial_op(
        context,
        pisa_op.Sub,
        PartialOpPolys(output, input0, input1, input_remaining_rns),
        PartialOpOptions(input0_last_q=True, input1_first_part=True),
        last_q,
    )


def muli_last_half(
    context: KernelContext,
    output: Polys,
    input0: Polys,
    input1: Polys,
    input_remaining_rns: Polys,
    last_q: int,
):
    """Muli input0/1 w/input0 last RNS"""
    return partial_op(
        context,
        pisa_op.Muli,
        PartialOpPolys(output, input0, input1, input_remaining_rns),
        PartialOpOptions(input0_last_q=True),
        last_q,
    )
