# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the kernel parser functionality.

This module contains tests for parsing kernel context, polynomial, and immediate
representations from string inputs, as well as for parsing various high-level
kernel operations. It verifies correct parsing for valid inputs and appropriate
error handling for invalid inputs.

Tested components:
- KernelContext, Polys, Immediate parsing from string representations.
- High-level kernel operations (Add, Muli, Copy, Square, Sub, Mul, Relin, Rotate,
    Rescale, NTT, INTT, Mod, ModUp) parsing from kernel string descriptions.
- Error handling for invalid input strings and unknown kernel operations.

Dependencies:
- pytest for test execution and exception checking.
- kernel_parser.parser.KernelParser for parsing logic.
- high_parser.types for data types.
- pisa_generators.* for kernel operation classes.
"""

from kernel_parser.parser import KernelParser
from high_parser.types import KernelContext, Polys, Immediate
from pisa_generators.basic import Copy, Add, Sub, Mul, Muli
from pisa_generators.ntt import NTT, INTT
from pisa_generators.square import Square
from pisa_generators.relin import Relin
from pisa_generators.rotate import Rotate
from pisa_generators.mod import Mod, ModUp
from pisa_generators.rescale import Rescale
import pytest


def test_parse_context_valid():
    """Test parsing of a valid KernelContext string."""
    s = (
        "KernelContext(scheme='CKKS', poly_order=16, key_rns=5, current_rns=3, "
        "max_rns=4, num_digits=None, label='foo')"
    )
    ctx = KernelParser.parse_context(s)
    assert isinstance(ctx, KernelContext)
    assert ctx.scheme == "CKKS"
    assert ctx.poly_order == 16
    assert ctx.key_rns == 5
    assert ctx.current_rns == 3
    assert ctx.max_rns == 4
    assert ctx.label == "foo"


def test_parse_context_invalid():
    """Test parsing of an invalid KernelContext string."""
    with pytest.raises(ValueError):
        KernelParser.parse_context("invalid string")


def test_parse_polys_valid():
    """Test parsing of a valid Polys string."""
    s = "Polys(name=bar, parts=2, rns=3)"
    polys = KernelParser.parse_polys(s)
    assert isinstance(polys, Polys)
    assert polys.name == "bar"
    assert polys.parts == 2
    assert polys.rns == 3


def test_parse_polys_invalid():
    """Test parsing of an invalid Polys string."""
    with pytest.raises(ValueError):
        KernelParser.parse_polys("bad string")


def test_parse_immediate_valid():
    """Test parsing of a valid Immediate string."""
    s = "Immediate(name='imm', rns=4)"
    imm = KernelParser.parse_immediate(s)
    assert isinstance(imm, Immediate)
    assert imm.name == "imm"
    assert imm.rns == 4


def test_parse_immediate_none_rns():
    """Test parsing of an Immediate string with None as rns."""
    s = "Immediate(name='imm', rns=None)"
    imm = KernelParser.parse_immediate(s)
    assert imm.rns is None


def test_parse_immediate_invalid():
    """Test parsing of an invalid Immediate string."""
    with pytest.raises(ValueError):
        KernelParser.parse_immediate("bad string")


# Common strings for reuse
BASE_CONTEXT = "context=KernelContext(scheme='CKKS', poly_order=16, key_rns=5, current_rns=3, max_rns=4, num_digits=None, label='foo')"
POLYS_OUT = "output=Polys(name=out, parts=2, rns=3)"
POLYS_IN0 = "input0=Polys(name=in0, parts=2, rns=3)"
POLYS_IN1 = "input1=Polys(name=in1, parts=2, rns=3)"
IMMEDIATE = "input1=Immediate(name='imm', rns=4)"


# Test cases for parsing high-level operations
@pytest.mark.parametrize(
    "kernel_str, expected_type, expected_attrs",
    [
        (
            f"### Kernel (0): Add({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0}, {POLYS_IN1})",
            Add,
            {"output.name": "out", "input0.name": "in0", "input1.name": "in1"},
        ),
        (
            f"### Kernel (1): Muli({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0}, {IMMEDIATE})",
            Muli,
            {
                "output.name": "out",
                "input0.name": "in0",
                "input1.name": "imm",
                "input1.rns": 4,
            },
        ),
        (
            f"### Kernel (2): Copy({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Copy,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (3): Square({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Square,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (4): Sub({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0}, {POLYS_IN1})",
            Sub,
            {"output.name": "out", "input0.name": "in0", "input1.name": "in1"},
        ),
        (
            f"### Kernel (5): Mul({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0}, {POLYS_IN1})",
            Mul,
            {"output.name": "out", "input0.name": "in0", "input1.name": "in1"},
        ),
        (
            f"### Kernel (6): Relin({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Relin,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (7): Rotate({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Rotate,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (8): Rescale({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Rescale,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (9): NTT({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            NTT,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (10): INTT({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            INTT,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (11): Mod({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            Mod,
            {"output.name": "out", "input0.name": "in0"},
        ),
        (
            f"### Kernel (12): ModUp({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})",
            ModUp,
            {"output.name": "out", "input0.name": "in0"},
        ),
    ],
)
def test_parse_high_op(kernel_str, expected_type, expected_attrs):
    """Test parsing of various HighOps."""
    op = KernelParser.parse_high_op(kernel_str)
    assert isinstance(op, expected_type)
    for attr_path, expected_value in expected_attrs.items():
        # Dynamically access nested attributes
        obj = op
        for attr in attr_path.split("."):
            obj = getattr(obj, attr)
        assert obj == expected_value


def test_parse_high_op_invalid():
    """Test parsing of an invalid HighOp."""
    s = f"### Kernel (13): UnknownOp({BASE_CONTEXT}, {POLYS_OUT}, {POLYS_IN0})"
    with pytest.raises(ValueError):
        KernelParser.parse_high_op(s)
