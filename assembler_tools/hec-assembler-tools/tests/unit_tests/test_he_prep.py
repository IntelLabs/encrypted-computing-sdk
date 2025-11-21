# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for he_prep module.
"""

import io
import os
import pathlib
import sys
from unittest import mock

import he_prep
import pytest


def _make_args(**overrides):
    defaults = {
        "input_file_name": "",
        "output_file_name": "",
        "mem_file": "",
        "verbose": 0,
        "split_on": False,
        "split_inst_limit": float("inf"),
        "split_vars_limit": float("inf"),
        "strategy": "largest_first",
        "interchange": False,
    }
    defaults.update(overrides)
    return mock.Mock(**defaults)


def test_main_assigns_and_saves(monkeypatch, tmp_path):
    """
    @brief Test that the main function assigns register banks, processes instructions, and saves the output.

    @details This test uses monkeypatching to mock dependencies and verifies that the output file
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
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock())

    he_prep.main(
        _make_args(
            input_file_name=str(input_file),
            output_file_name=str(output_file),
        )
    )
    # Output file should contain the instruction
    assert output_file.read_text().strip() == "inst1"


def test_main_no_input_file():
    """
    @brief Test that main raises an error when no input file is provided.
    """
    with pytest.raises(FileNotFoundError):
        he_prep.main(_make_args())  # Should raise an error due to missing input file


def test_main_no_output_file():
    """
    @brief Test that main raises an error when no output file is provided.
    """
    with pytest.raises(FileNotFoundError):
        he_prep.main(_make_args(input_file_name="input.csv"))  # Should raise an error due to missing output file


def test_main_no_instructions(monkeypatch):
    """
    @brief Test that main handles the case where no instructions are processed.

    @details This test checks that the function can handle an empty instruction list without errors.
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
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock())

    he_prep.main(
        _make_args(
            input_file_name=input_file,
            output_file_name=output_file,
        )
    )

    # Output file should be empty
    output_file_path = pathlib.Path(output_file)
    assert not output_file_path.exists() or output_file_path.read_text(encoding="utf-8").strip() == ""


def test_main_invalid_input_file(tmp_path):
    """
    @brief Test that main raises an error when the input file does not exist.
    """
    input_file = tmp_path / "non_existent.csv"
    output_file = tmp_path / "output.csv"

    with pytest.raises(FileNotFoundError):
        he_prep.main(
            _make_args(
                input_file_name=str(input_file),
                output_file_name=str(output_file),
            )
        )  # Should raise an error due to missing input file


def test_main_invalid_output_file(tmp_path):
    """
    @brief Test that main raises an error when the output file cannot be created.

    @details This test checks that the function handles file permission errors gracefully.
    """
    input_file = tmp_path / "input.csv"
    input_file.write_text("")  # Write empty string to avoid SyntaxError
    output_file = tmp_path / "output.csv"

    # Make the output file read-only
    output_file.touch()
    os.chmod(output_file, 0o444)  # Read-only permissions

    with pytest.raises(PermissionError):
        he_prep.main(
            _make_args(
                input_file_name=str(input_file),
                output_file_name=str(output_file),
            )
        )  # Should raise an error due to permission issues


def test_main_respects_coloring_strategy(monkeypatch, tmp_path):
    """
    @brief Test that main respects the coloring strategy and interchange options.

    @details This test verifies that the assigned register banks strategy and interchange options
             are correctly passed to the assign_register_banks_to_vars function.
    """
    input_file = tmp_path / "input.csv"
    input_file.write_text("dummy")
    output_file = tmp_path / "output.csv"
    dummy_model = object()
    dummy_insts = [mock.Mock(to_pisa_format=mock.Mock(return_value="inst"))]
    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=dummy_insts),
    )
    assign_mock = mock.Mock()
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", assign_mock)

    he_prep.main(
        _make_args(
            input_file_name=str(input_file),
            output_file_name=str(output_file),
            strategy="smallest_last",
            interchange=True,
        )
    )

    assign_mock.assert_called_once()
    _, kwargs = assign_mock.call_args
    assert kwargs["strategy"] == "smallest_last"
    assert kwargs["interchange"] is True


def test_parse_args():
    """
    @brief Test that parse_args returns the expected arguments.
    """
    test_args = [
        "prog",
        "input.csv",
        "output.csv",
        "--isa_spec",
        "isa.json",
        "--mem_spec",
        "mem.json",
        "--mem_file",
        "kernel.mem",
        "--split_vars_limit",
        "10",
        "--split_inst_limit",
        "5",
        "--strategy",
        "smallest_last",
        "--interchange",
        "-vv",
    ]
    with mock.patch.object(sys, "argv", test_args):
        args = he_prep.parse_args()

    assert args.input_file_name == "input.csv"
    assert args.output_file_name == "output.csv"
    assert args.isa_spec_file == "isa.json"
    assert args.mem_spec_file == "mem.json"
    assert args.mem_file == "kernel.mem"
    assert args.split_vars_limit == 10.0
    assert args.split_inst_limit == 5.0
    assert args.split_on is True
    assert args.strategy == "smallest_last"
    assert args.interchange is True
    assert args.verbose == 2


def test_save_pisa_listing():
    """
    @brief Test that save_pisa_listing writes instructions in correct format.
    """
    mock_inst1 = mock.Mock(to_pisa_format=mock.Mock(return_value="instruction1"))
    mock_inst2 = mock.Mock(to_pisa_format=mock.Mock(return_value="instruction2"))
    mock_inst3 = mock.Mock(to_pisa_format=mock.Mock(return_value=""))  # Empty line should be skipped

    output = io.StringIO()
    he_prep.save_pisa_listing(output, [mock_inst1, mock_inst2, mock_inst3])

    result = output.getvalue()
    assert "instruction1\n" in result
    assert "instruction2\n" in result
    assert result.count("\n") == 2  # Only 2 instructions written


def test_main_derives_default_output_filename(monkeypatch, tmp_path):
    """
    @brief Test that main derives output filename from input when not provided.
    """
    input_file = tmp_path / "kernel.pisa"
    input_file.write_text("dummy")

    dummy_model = object()
    dummy_insts = [mock.Mock(to_pisa_format=mock.Mock(return_value="inst"))]

    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=dummy_insts),
    )
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock())

    he_prep.main(
        _make_args(
            input_file_name=str(input_file),
            output_file_name="",  # Not provided
        )
    )

    # Should create kernel.tw.pisa
    expected_output = tmp_path / "kernel.tw.pisa"
    assert expected_output.exists()


def test_main_with_kernel_splitting(monkeypatch, tmp_path):
    """
    @brief Test that main handles kernel splitting when split_on is True.
    """
    input_file = tmp_path / "kernel.pisa"
    input_file.write_text("dummy")
    output_file = tmp_path / "output.pisa"

    dummy_model = object()
    dummy_insts = [mock.Mock(to_pisa_format=mock.Mock(return_value="inst"))]

    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=dummy_insts),
    )
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock())

    # Mock KernelSplitter
    mock_splitter = mock.Mock()
    split_file1 = tmp_path / "split1.pisa"
    split_file2 = tmp_path / "split2.pisa"
    mock_splitter.prepare_instruction_splits.return_value = [
        (dummy_insts, str(split_file1)),
        (dummy_insts, str(split_file2)),
    ]
    monkeypatch.setattr(he_prep, "KernelSplitter", mock.Mock(return_value=mock_splitter))

    he_prep.main(
        _make_args(
            input_file_name=str(input_file),
            output_file_name=str(output_file),
            split_on=True,
            split_inst_limit=10.0,
            split_vars_limit=5.0,
        )
    )

    # Verify splitter was called
    mock_splitter.prepare_instruction_splits.assert_called_once()
    # Verify both split files were created
    assert split_file1.exists()
    assert split_file2.exists()


def test_main_verbose_output(monkeypatch, tmp_path, capsys):
    """
    @brief Test that main prints verbose output when verbose flag is set.
    """
    input_file = tmp_path / "kernel.pisa"
    input_file.write_text("dummy")
    output_file = tmp_path / "output.pisa"

    dummy_model = object()
    dummy_insts = [mock.Mock(to_pisa_format=mock.Mock(return_value="inst"))] * 5

    monkeypatch.setattr(he_prep, "MemoryModel", mock.Mock(return_value=dummy_model))
    monkeypatch.setattr(
        he_prep.preprocessor,
        "preprocess_pisa_kernel_listing",
        mock.Mock(return_value=dummy_insts),
    )
    monkeypatch.setattr(he_prep.preprocessor, "assign_register_banks_to_vars", mock.Mock())

    he_prep.main(
        _make_args(
            input_file_name=str(input_file),
            output_file_name=str(output_file),
            verbose=1,
        )
    )

    captured = capsys.readouterr()
    assert "Assigning register banks to variables..." in captured.out
    assert "Instructions in input: 5" in captured.out
    assert "Saving..." in captured.out
    assert "Output:" in captured.out
    assert "Instructions in output: 5" in captured.out
    assert "Generation time:" in captured.out


def test_parse_args_defaults():
    """
    @brief Test that parse_args sets correct defaults when optional args not provided.
    """
    test_args = ["prog", "input.csv"]
    with mock.patch.object(sys, "argv", test_args):
        args = he_prep.parse_args()

    assert args.input_file_name == "input.csv"
    assert args.output_file_name is None
    assert args.isa_spec_file == ""
    assert args.mem_spec_file == ""
    assert args.mem_file == ""
    assert args.split_vars_limit == float("inf")
    assert args.split_inst_limit == float("inf")
    assert args.split_on is False
    assert args.strategy == "largest_first"
    assert args.interchange is False
    assert args.verbose == 0


def test_parse_args_split_on_without_mem_file_fails():
    """
    @brief Test that parse_args raises assertion error when split_on but no mem_file.
    """
    test_args = [
        "prog",
        "input.csv",
        "--split_inst_limit",
        "10",
    ]
    with mock.patch.object(sys, "argv", test_args):
        with pytest.raises(AssertionError, match="--mem_file must be specified"):
            he_prep.parse_args()
