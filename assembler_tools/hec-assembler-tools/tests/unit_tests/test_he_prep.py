# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for he_prep module.
"""

from unittest import mock
import os
import sys
import pathlib
import pytest
import he_prep


def test_main_assigns_and_saves(monkeypatch, tmp_path):
    """
    Test that the main function assigns register banks, processes instructions, and saves the output.

    This test uses monkeypatching to mock dependencies and verifies that the output file
    contains the expected instruction after processing a dummy input file.
    """
    # Prepare dummy input file
    input_file = tmp_path / "input.csv"
    input_file.write_text("dummy")
    output_file = tmp_path / "output.csv"

    dummy_model = object()
    dummy_insts = [mock.Mock(to_pisa_format=mock.Mock(return_value="inst1"))]

    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=dummy_insts),
    )
    monkeypatch.setattr(
        he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock()
    )

    he_prep.main(str(output_file), str(input_file), b_verbose=False)
    # Output file should contain the instruction
    assert output_file.read_text().strip() == "inst1"


def test_main_no_input_file():
    """
    Test that main raises an error when no input file is provided.
    """
    with pytest.raises(FileNotFoundError):
        he_prep.main(
            "", "", b_verbose=False
        )  # Should raise an error due to missing input file


def test_main_no_output_file():
    """
    Test that main raises an error when no output file is provided.
    """
    with pytest.raises(FileNotFoundError):
        he_prep.main(
            "", "input.csv", b_verbose=False
        )  # Should raise an error due to missing output file


def test_main_no_instructions(monkeypatch):
    """
    Test that main handles the case where no instructions are processed.

    This test checks that the function can handle an empty instruction list without errors.
    """
    input_file = "empty_input.csv"
    output_file = "empty_output.csv"

    with open(input_file, "w", encoding="utf-8") as f:
        f.write("")  # Create an empty input file

    dummy_model = object()
    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=[]),
    )
    monkeypatch.setattr(
        he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock()
    )

    he_prep.main(output_file, input_file, b_verbose=False)

    # Output file should be empty
    output_file_path = pathlib.Path(output_file)
    assert (
        not output_file_path.exists()
        or output_file_path.read_text(encoding="utf-8").strip() == ""
    )


def test_main_invalid_input_file(tmp_path):
    """
    Test that main raises an error when the input file does not exist.
    """
    input_file = tmp_path / "non_existent.csv"
    output_file = tmp_path / "output.csv"

    with pytest.raises(FileNotFoundError):
        he_prep.main(
            str(output_file), str(input_file), b_verbose=False
        )  # Should raise an error due to missing input file


def test_main_invalid_output_file(tmp_path):
    """
    Test that main raises an error when the output file cannot be created.
    This test checks that the function handles file permission errors gracefully.
    """
    input_file = tmp_path / "input.csv"
    input_file.write_text("")  # Write empty string to avoid SyntaxError
    output_file = tmp_path / "output.csv"

    # Make the output file read-only
    output_file.touch()
    os.chmod(output_file, 0o444)  # Read-only permissions

    with pytest.raises(PermissionError):
        he_prep.main(
            str(output_file), str(input_file), b_verbose=False
        )  # Should raise an error due to permission issues


def test_parse_args():
    """
    Test that parse_args returns the expected arguments.
    """
    test_args = [
        "prog",
        "input.csv",
        "output.csv",
        "--isa_spec",
        "isa.json",
        "--mem_spec",
        "mem.json",
        "--verbose",
    ]
    with mock.patch.object(sys, "argv", test_args):
        args = he_prep.parse_args()

    assert args.output_file_name == "output.csv"
    assert args.input_file_name == "input.csv"
    assert args.isa_spec_file == "isa.json"
    assert args.mem_spec_file == "mem.json"
    assert args.verbose == 1
