# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_trace_info.py
@brief Unit tests for the TraceInfo module and related classes
"""
from unittest.mock import patch, mock_open
import pytest

from linker.kern_trace.trace_info import KernelFiles, TraceInfo
from linker.kern_trace.context_config import ContextConfig
from linker.kern_trace.kernel_op import KernelOp


class TestKernelFiles:
    """
    @class TestKernelFiles
    @brief Test cases for the KernelFiles class
    """

    def test_kernel_files_creation(self):
        """
        @brief Test KernelFiles creation and attribute access
        """
        # Act
        kernel_files = KernelFiles(
            directory="/tmp/dir",
            prefix="prefix",
            minst="prefix.minst",
            cinst="prefix.cinst",
            xinst="prefix.xinst",
            mem="prefix.mem",
        )

        # Assert
        assert kernel_files.directory == "/tmp/dir"
        assert kernel_files.prefix == "prefix"
        assert kernel_files.minst == "prefix.minst"
        assert kernel_files.cinst == "prefix.cinst"
        assert kernel_files.xinst == "prefix.xinst"
        assert kernel_files.mem == "prefix.mem"

    def test_kernel_files_without_mem(self):
        """
        @brief Test KernelFiles creation without mem file
        """
        # Act
        kernel_files = KernelFiles(
            directory="/tmp/dir",
            prefix="prefix",
            minst="prefix.minst",
            cinst="prefix.cinst",
            xinst="prefix.xinst",
        )

        # Assert
        assert kernel_files.directory == "/tmp/dir"
        assert kernel_files.prefix == "prefix"
        assert kernel_files.minst == "prefix.minst"
        assert kernel_files.cinst == "prefix.cinst"
        assert kernel_files.xinst == "prefix.xinst"
        assert kernel_files.mem is None


class TestTraceInfo:
    """
    @class TestTraceInfo
    @brief Test cases for the TraceInfo class
    """

    def test_init(self):
        """
        @brief Test initialization of TraceInfo class
        """
        # Arrange & Act
        trace_info = TraceInfo("/path/to/trace.txt")

        # Assert
        assert trace_info.get_trace_file() == "/path/to/trace.txt"

    def test_str_representation(self):
        """
        @brief Test string representation of TraceInfo
        """
        # Arrange
        trace_info = TraceInfo("/path/to/trace.txt")

        # Act
        result = str(trace_info)

        # Assert
        assert "TraceFile" in result
        assert "/path/to/trace.txt" in result

    def test_get_param_index_dict(self):
        """
        @brief Test get_param_index_dict method
        """
        # Arrange
        trace_info = TraceInfo("/path/to/trace.txt")
        tokens = [
            "instruction",
            "scheme",
            "poly_modulus_degree",
            "keyrns_terms",
            "arg0",
            "arg1",
        ]

        # Act
        result = trace_info.get_param_index_dict(tokens)

        # Assert
        assert isinstance(result, dict)
        assert len(result) == len(tokens)
        assert result["instruction"] == 0
        assert result["scheme"] == 1
        assert result["poly_modulus_degree"] == 2
        assert result["keyrns_terms"] == 3
        assert result["arg0"] == 4
        assert result["arg1"] == 5

    def test_extract_context_and_args(self):
        """
        @brief Test extract_context_and_args method
        """
        # Arrange
        trace_info = TraceInfo("/path/to/trace.txt")
        tokens = ["kernel1", "CKKS", "8192", "2", "input_var", "output_var"]
        param_idxs = {
            "instruction": 0,
            "scheme": 1,
            "poly_modulus_degree": 2,
            "keyrns_terms": 3,
            "arg0": 4,
            "arg1": 5,
        }

        # Act
        name, context_config, kern_args = trace_info.extract_context_and_args(
            tokens, param_idxs, 1
        )

        # Assert
        assert name == "kernel1"
        assert isinstance(context_config, ContextConfig)
        assert context_config.scheme == "CKKS"
        assert context_config.poly_mod_degree == 8192
        assert context_config.keyrns_terms == 2
        assert kern_args == ["input_var", "output_var"]

    def test_extract_context_and_args_missing_param(self):
        """
        @brief Test extract_context_and_args with missing parameter
        """
        # Arrange
        trace_info = TraceInfo("/path/to/trace.txt")
        tokens = ["kernel1", "CKKS", "8192", "2", "input_var", "output_var"]
        param_idxs = {
            "instruction": 0,
            "scheme": 1,
            # Missing "poly_modulus_degree"
            "keyrns_terms": 3,
            "arg0": 4,
            "arg1": 5,
        }

        # Act & Assert
        with pytest.raises(KeyError, match="poly_modulus_degree"):
            trace_info.extract_context_and_args(tokens, param_idxs, 1)

    def test_extract_context_and_args_invalid_number(self):
        """
        @brief Test extract_context_and_args with invalid number
        """
        # Arrange
        trace_info = TraceInfo("/path/to/trace.txt")
        tokens = ["kernel1", "CKKS", "invalid", "2", "input_var", "output_var"]
        param_idxs = {
            "instruction": 0,
            "scheme": 1,
            "poly_modulus_degree": 2,  # Will try to convert "invalid" to int
            "keyrns_terms": 3,
            "arg0": 4,
            "arg1": 5,
        }

        # Act & Assert
        with pytest.raises(ValueError):
            trace_info.extract_context_and_args(tokens, param_idxs, 1)

    def test_parse_kernel_ops_with_valid_trace(self):
        """
        @brief Test parse_kernel_ops with a valid trace file
        """
        # Arrange
        trace_file = "/path/to/trace.txt"
        trace_content = (
            "instruction scheme poly_modulus_degree keyrns_terms arg0 arg1\n"
            "kernel1 CKKS 8192 2 input_var output_var\n"
            "kernel2 BFV 4096 1 input_var2 output_var2\n"
        )

        # Act
        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_open(read_data=trace_content)
        ), patch("linker.kern_trace.trace_info.tokenize_from_line") as mock_tokenize:

            # Mock the tokenize_from_line function to return expected tokens
            mock_tokenize.side_effect = [
                (
                    [
                        "instruction",
                        "scheme",
                        "poly_modulus_degree",
                        "keyrns_terms",
                        "arg0",
                        "arg1",
                    ],
                    None,
                ),
                (
                    ["add", "CKKS", "8192", "2", "input_var1-0-1", "output_var0-0-1"],
                    None,
                ),
                (
                    ["mul", "BFV", "4096", "1", "input_var2-3-4", "output_var0-2-2"],
                    None,
                ),
            ]

            trace_info = TraceInfo(trace_file)
            result = trace_info.parse_kernel_ops()

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], KernelOp)
        assert isinstance(result[1], KernelOp)
        assert result[0].expected_in_kern_file_name == "ckks_add_8192_l1_m2"
        assert result[1].expected_in_kern_file_name == "bfv_mul_4096_l2_m1"
        assert len(result[0].kern_vars) == 2
        assert len(result[1].kern_vars) == 2

    def test_parse_kernel_ops_with_empty_trace(self):
        """
        @brief Test parse_kernel_ops with an empty trace file
        """
        # Arrange
        trace_file = "/path/to/empty_trace.txt"

        # Act
        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_open(read_data="")
        ):

            trace_info = TraceInfo(trace_file)
            result = trace_info.parse_kernel_ops()

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    def test_parse_kernel_ops_with_nonexistent_file(self):
        """
        @brief Test parse_kernel_ops with a nonexistent file
        """
        # Arrange
        trace_file = "/path/to/nonexistent.txt"

        # Act & Assert
        with patch("os.path.isfile", return_value=False):
            trace_info = TraceInfo(trace_file)
            with pytest.raises(FileNotFoundError):
                trace_info.parse_kernel_ops()

    def test_parse_kernel_ops_skip_empty_lines(self):
        """
        @brief Test parse_kernel_ops skips empty lines
        """
        # Arrange
        trace_file = "/path/to/trace.txt"
        trace_content = (
            "instruction scheme poly_modulus_degree keyrns_terms arg0 arg1\n"
            "\n"  # Empty line
            "kernel1 CKKS 8192 2 input_var output_var\n"
            "   \n"  # Line with whitespace
            "kernel2 BFV 4096 1 input_var2 output_var2\n"
        )

        # Act
        with patch("os.path.isfile", return_value=True), patch(
            "builtins.open", mock_open(read_data=trace_content)
        ), patch("linker.kern_trace.trace_info.tokenize_from_line") as mock_tokenize:

            # Mock the tokenize_from_line function to return expected tokens
            mock_tokenize.side_effect = [
                (
                    [
                        "instruction",
                        "scheme",
                        "poly_modulus_degree",
                        "keyrns_terms",
                        "arg0",
                        "arg1",
                    ],
                    None,
                ),
                ([], None),  # Empty line
                (
                    ["add", "CKKS", "8192", "2", "input_var1-0-2", "output_var0-3-2"],
                    None,
                ),
                ([""], None),  # Line with whitespace tokenizes to empty string
                (
                    ["mul", "BGV", "4096", "1", "input_var2-3-4", "output_var2-3-3"],
                    None,
                ),
            ]

            trace_info = TraceInfo(trace_file)
            result = trace_info.parse_kernel_ops()

        # Assert
        assert len(result) == 2  # Only 2 valid kernel operations
        assert isinstance(result[0], KernelOp)
        assert isinstance(result[1], KernelOp)
