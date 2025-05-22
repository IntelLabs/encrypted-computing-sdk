# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Test the expected behaviour of the kerngen script"""

from enum import Enum
from pathlib import Path
from subprocess import run
from high_parser.parser import ParseResults
from high_parser.types import Context
import pytest


class Op(Enum):
    """Enum class of valid high opnames and corresponding low ops"""

    ADD = "add"
    MUL = "mul"


def execute_process(cmd: list[str], data_in=None):
    """Helper function for executing processes. stdout and stderr are always
    captured. NOTE: subprocess.run will fail silently with a non-zero exit code
    so always check the returncode"""
    return run(
        list(map(str, cmd)),
        input=data_in,
        capture_output=True,
        check=False,
        encoding="utf-8",
    )


@pytest.mark.parametrize("gen_op_data", ["ADD", "MUL"], indirect=True)
def test_op(kerngen_path, gen_op_data):
    """Test kerngen outputs correct data based on input for various operations"""
    input_string, expected_out = gen_op_data
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert expected_out in result.stdout
    assert not result.stderr
    assert result.returncode == 0


def test_missing_context(kerngen_path):
    """Test kerngen raises an exception when context is not the first line of
    input"""
    input_string = "ADD a b c\nCONTEXT BGV 16384 4 3\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert "RuntimeError: No `CONTEXT` provided before `ADD a b c`" in result.stderr
    assert result.returncode != 0


def test_multiple_contexts(kerngen_path):
    """Test kerngen raises an exception when more than one context is given"""
    input_string = "CONTEXT BGV 16384 4 2\nData a 2\nCONTEXT BGV 16384 4 2\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert "RuntimeError: Second context given" in result.stderr
    assert result.returncode != 0


def test_context_options_without_key(kerngen_path):
    """Test kerngen raises an exception when more than one context is given"""
    input_string = "CONTEXT BGV 16384 3 2 1\nData a 2\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert (
        "ValueError: Options must be key/value pairs (e.g. num_digits=3): '1'"
        in result.stderr
    )
    assert result.returncode != 0


def test_context_unsupported_options_variable(kerngen_path):
    """Test kerngen raises an exception when more than one context is given"""
    input_string = "CONTEXT BGV 16384 3 2 test=3\nData a 2\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert "Invalid options name: 'test'" in result.stderr
    assert result.returncode != 0


@pytest.mark.parametrize("invalid", [-1, 256, 0.1, "str"])
def test_context_option_invalid_values(kerngen_path, invalid):
    """Test kerngen raises an exception if value is out of range for correct key"""
    input_string = f"CONTEXT BGV 16384 3 2 num_digits={invalid}\nData a 2\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert (
        f"ValueError: Options must be key/value pairs (e.g. num_digits=3): 'num_digits={invalid}'"
        in result.stderr
    )
    assert result.returncode != 0


def test_unrecognised_opname(kerngen_path):
    """Test kerngen raises an exception when receiving an unrecognised
    opname"""
    input_string = "CONTEXT BGV 16384 3 2\nOPERATION a b c\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert (
        "GeneratorError: Op not found in available pisa ops: OPERATION" in result.stderr
    )
    assert result.returncode != 0


def test_invalid_scheme(kerngen_path):
    """Test kerngen raises an exception when receiving an invalid scheme"""
    input_string = "CONTEXT SCHEME 16384 4 3\nADD a b c\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert "GeneratorError: Scheme `SCHEME` not found in manifest file" in result.stderr
    assert result.returncode != 0


@pytest.mark.parametrize("invalid_poly", [16000, 2**12, 2**13, 2**18])
def test_invalid_poly_order(kerngen_path, invalid_poly):
    """Poly order should be powers of two >= 2^14 and <= 2^17"""
    input_string = "CONTEXT BGV " + str(invalid_poly) + " 4 3\nADD a b c\n"
    result = execute_process(
        [kerngen_path],
        data_in=input_string,
    )
    assert not result.stdout
    assert (
        "ValueError: Poly order `" + str(invalid_poly) + "` must be power of two >="
        in result.stderr
    )
    assert result.returncode != 0


def test_parse_results_missing_context():
    """Test ParseResults constructor for missing context"""
    with pytest.raises(LookupError) as e:
        parse_results = ParseResults([], {})
        print(parse_results.context)  # will generate a lookup error
    assert "No Context found for commands list for ParseResults" in str(e.value)


def test_parse_results_multiple_context():
    """Test ParseResults constructor for multiple context"""
    with pytest.raises(LookupError) as e:
        parse_results = ParseResults(
            [
                Context(
                    scheme="BGV", poly_order=16384, key_rns=2, current_rns=1, max_rns=1
                ),
                Context(
                    scheme="CKKS", poly_order=16384, key_rns=2, current_rns=1, max_rns=1
                ),
            ],
            {},
        )
        print(parse_results.context)  # will raise a LookupError
    assert "Multiple Context found in commands list for ParseResults" in str(e.value)


@pytest.fixture(name="gen_op_data")
def fixture_gen_op_data(request):
    """Given an op name, return both the input and expected output strings"""
    in_lines = (
        "CONTEXT BGV 16384 4 3",
        "Data a 2",
        "Data b 2",
        "Data c 2",
        f"{request.param} a b c",
    )
    # TODO: Build this string properly
    out = f"0, {Op[request.param].value}, a_0_0_0, b_0_0_0, c_0_0_0, 0"
    return "\n".join(in_lines), out


@pytest.fixture(name="kerngen_path")
def fixture_kerngen_path() -> Path:
    """Returns the absolute path to the `kerngen.py` script"""
    return Path(__file__).resolve().parent.parent / "kerngen.py"
