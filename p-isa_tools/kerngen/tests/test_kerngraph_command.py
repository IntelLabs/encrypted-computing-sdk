# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""
Unit tests for the `parse_args` function from the `kerngraph` module.

These tests verify the correct parsing of command-line arguments, including:
- Default argument values.
- Handling of the debug flag.
- Parsing multiple target arguments.
- Valid and invalid combinations of primary and secondary loop keys.
- Error handling for invalid argument values.

Helper:
- `run_parse_args_with_args`: Temporarily sets `sys.argv` to simulate command-line input for testing.

Test Cases:
- `test_parse_args_defaults`: Checks default argument values.
- `test_parse_args_debug_flag`: Checks enabling the debug flag.
- `test_parse_args_target_multiple`: Checks parsing multiple targets.
- `test_parse_args_primary_secondary_valid`: Checks valid primary and secondary loop key combinations.
- `test_parse_args_primary_secondary_same`: Ensures error is raised if primary and secondary keys are the same.
- `test_parse_args_invalid_primary_secondary`: Ensures error is raised for invalid primary or secondary key values.
"""

import sys
from argparse import Namespace

import pytest
from const.options import LoopKey
from kerngraph import parse_args


def run_parse_args_with_args(args):
    """Helper to run parse_args with specific sys.argv"""
    sys_argv_backup = sys.argv
    sys.argv = ["kerngraph.py"] + args
    try:
        return parse_args()
    finally:
        sys.argv = sys_argv_backup


def test_parse_args_defaults():
    """Test default argument values for parse_args."""
    args = run_parse_args_with_args([])
    assert isinstance(args, Namespace)
    assert args.debug is False
    assert args.target == []
    assert args.primary == LoopKey.PART


def test_parse_args_debug_flag():
    """Test enabling the debug flag."""
    args = run_parse_args_with_args(["-d"])
    assert args.debug is True


def test_parse_args_target_multiple():
    """Test parsing multiple target arguments."""
    args = run_parse_args_with_args(["-t", "add", "sub"])
    assert args.target == ["add", "sub"]


def test_parse_args_primary_secondary_valid():
    """Test valid primary and secondary loop key combinations."""
    args = run_parse_args_with_args(["-p", "rns", "-s", "part"])
    assert args.primary == LoopKey.RNS
    assert args.secondary == LoopKey.PART


def test_parse_args_primary_secondary_same():
    """Test that primary and secondary keys cannot be the same."""
    sys_argv_backup = sys.argv
    sys.argv = ["kerngraph.py", "-p", "rns", "-s", "rns"]
    with pytest.raises(ValueError, match="Primary and secondary keys cannot be the same."):
        parse_args()
    sys.argv = sys_argv_backup


def test_parse_args_invalid_primary_secondary():
    """Test that invalid primary or secondary keys raise an error."""
    for flag in ["-p", "-s"]:
        with pytest.raises(SystemExit) as excinfo:
            run_parse_args_with_args([flag, "invalid"])
        assert excinfo.value.code != 0  # Ensure the exit code indicates an error
