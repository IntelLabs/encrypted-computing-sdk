# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link_utils.py
@brief Unit tests for the he_link_utils module
"""

from unittest.mock import MagicMock, mock_open, patch

import pytest
from assembler.common import constants
from linker.he_link_utils import (
    initialize_memory_model,
    prepare_input_files,
    prepare_output_files,
    remap_vars,
    update_input_prefixes,
)
from linker.kern_trace.trace_info import KernelInfo


class TestHelperFunctions:
    """
    @class TestHelperFunctions
    @brief Test cases for helper functions in he_link_utils
    """

    def test_prepare_output_files(self):
        """
        @brief Test prepare_output_files function creates correct output files
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.output_dir = "/tmp"
        mock_config.output_prefix = "output"
        mock_config.using_trace_file = False

        # Act
        with (
            patch("os.path.dirname", return_value="/tmp"),
            patch("pathlib.Path.mkdir"),
            patch("assembler.common.makeUniquePath", side_effect=lambda x: x),
        ):
            result = prepare_output_files(mock_config)

        # Assert
        assert result.directory == "/tmp"
        assert result.prefix == "output"
        assert result.minst == "/tmp/output.minst"
        assert result.cinst == "/tmp/output.cinst"
        assert result.xinst == "/tmp/output.xinst"
        assert result.mem is None

    def test_prepare_output_files_with_mem(self):
        """
        @brief Test prepare_output_files with using_trace_file=True
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.output_dir = "/tmp"
        mock_config.output_prefix = "output"
        mock_config.using_trace_file = True

        # Act
        with (
            patch("os.path.dirname", return_value="/tmp"),
            patch("pathlib.Path.mkdir"),
            patch("assembler.common.makeUniquePath", side_effect=lambda x: x),
        ):
            result = prepare_output_files(mock_config)

        # Assert
        assert result.directory == "/tmp"
        assert result.prefix == "output"
        assert result.minst == "/tmp/output.minst"
        assert result.cinst == "/tmp/output.cinst"
        assert result.xinst == "/tmp/output.xinst"
        assert result.mem == "/tmp/output.mem"

    def test_prepare_input_files(self):
        """
        @brief Test prepare_input_files function
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_dir = "/tmp"
        mock_config.input_prefixes = ["input1", "input2"]
        mock_config.using_trace_file = False

        mock_output_files = KernelInfo(
            {
                "directory": "/tmp",
                "prefix": "output",
                "minst": "/tmp/output.minst",
                "cinst": "/tmp/output.cinst",
                "xinst": "/tmp/output.xinst",
            }
        )

        # Act
        with patch("os.path.isfile", return_value=True), patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
            result = prepare_input_files(mock_config, mock_output_files)

        # Assert
        assert len(result) == 2
        assert result[0].directory == "/tmp"
        assert result[0].prefix == "input1"
        assert result[0].minst == "/tmp/input1.minst"
        assert result[0].cinst == "/tmp/input1.cinst"
        assert result[0].xinst == "/tmp/input1.xinst"
        assert result[0].mem is None
        assert result[1].prefix == "input2"

    def test_prepare_input_files_file_not_found(self):
        """
        @brief Test prepare_input_files when a file doesn't exist
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_dir = "/tmp"
        mock_config.input_prefixes = ["input1"]
        mock_config.using_trace_file = False

        mock_output_files = KernelInfo(
            {
                "directory": "/tmp",
                "prefix": "output",
                "minst": "/tmp/output.minst",
                "cinst": "/tmp/output.cinst",
                "xinst": "/tmp/output.xinst",
                "mem": None,
            }
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=False), patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
            with pytest.raises(FileNotFoundError):
                prepare_input_files(mock_config, mock_output_files)

    def test_prepare_input_files_output_conflict(self):
        """
        @brief Test prepare_input_files when input and output files conflict
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_dir = "/tmp"
        mock_config.input_prefixes = ["input1"]
        mock_config.using_trace_file = False

        # Output file matching an input file
        output_files = KernelInfo(
            {
                "directory": "/tmp",
                "prefix": "output",
                "minst": "/tmp/input1.minst",  # Conflict
                "cinst": "/tmp/output.cinst",
                "xinst": "/tmp/output.xinst",
                "mem": None,
            }
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=True), patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
            with pytest.raises(RuntimeError):
                prepare_input_files(mock_config, output_files)

    def test_update_input_prefixes(self):
        """
        @brief Test update_input_prefixes correctly processes a trace file and returns kernel operations dictionary
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_prefixes = []

        # Create mock kernel ops with expected_in_kern_file_name attribute
        mock_kernel_op1 = MagicMock()
        mock_kernel_op1.expected_in_kern_file_name = "kernel1"

        mock_kernel_op2 = MagicMock()
        mock_kernel_op2.expected_in_kern_file_name = "kernel2"

        mock_kernel_ops = [mock_kernel_op1, mock_kernel_op2]

        # Act
        # with patch("linker.he_link_utils.TraceInfo") as mock_trace_info_class:
        # Configure the mock TraceInfo instance
        #    mock_trace_info = mock_trace_info_class.return_value
        #    mock_trace_info.parse_kernel_ops.return_value = mock_kernel_ops

        # Call the function under test
        update_input_prefixes(mock_kernel_ops, mock_config)

        # Assert
        # Verify the input_prefixes were updated in the run_config
        assert mock_config.input_prefixes == ["kernel1_pisa.tw", "kernel2_pisa.tw"]

    def test_update_input_prefixes_with_empty_kernel_ops(self):
        """
        @brief Test update_input_prefixes correctly handles empty kernel operations
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_prefixes = ["should_be_cleared"]
        mock_kernel_ops = []  # Empty list of kernel ops

        # Act
        # Call the function under test with empty kernel_ops list
        update_input_prefixes(mock_kernel_ops, mock_config)

        # Assert
        # Verify the input_prefixes were updated (cleared) in the run_config
        assert not mock_config.input_prefixes

    def _create_kernel_test_data(self):
        """
        @brief Helper method to create test data for remap_vars tests
        @return Tuple containing test data: (kernels_files, kernels_dinstrs, kernel_ops, expected_dicts)
        """
        # Create mock kernel files
        mock_files = []
        for i in range(1, 3):
            kernel_file = MagicMock(spec=KernelInfo)
            kernel_file.prefix = f"kernel{i}_pisa.tw"
            kernel_file.mem = f"/path/to/kernel{i}.mem"
            mock_files.append(kernel_file)

        # Create mock kernel operations
        kernel_ops = []
        for i in range(1, 3):
            kernel_op = MagicMock()
            kernel_op.expected_in_kern_file_name = f"kernel{i}"
            kernel_ops.append(kernel_op)

        # Create test dinstructions data
        dinstrs = []
        for i in range(1, 4):
            dinstr = MagicMock()
            dinstr.var = f"var{i}"
            dinstrs.append(dinstr)

        # Setup test data structures
        kernel_dinstrs = [
            [dinstrs[0]],  # kernel1 dinstrs
            [dinstrs[1], dinstrs[2]],  # kernel2 dinstrs
        ]

        # Expected remap dictionaries
        expected_dicts = {
            "var1": "mapped_var1",
            "var2": "mapped_var2",
            "var3": "mapped_var3",
        }

        # Pack test data
        test_data = {
            "files": mock_files,
            "kernel_ops": kernel_ops,
            "dinstrs": dinstrs,
            "kernel_dinstrs": kernel_dinstrs,
            "expected_dicts": expected_dicts,
            "joined_dinstrs": dinstrs,  # All dinstrs joined
        }

        return test_data

    def test_remap_vars_with_multiple_kernels(self):
        """
        @brief Test remap_vars with multiple input kernel files
        """
        # Arrange - Get test data from helper method
        test_data = self._create_kernel_test_data()

        # Act
        with patch("linker.he_link_utils.remap_dinstrs_vars") as mock_remap_vars:
            # Configure mocks
            mock_remap_vars.side_effect = [
                test_data["expected_dicts"],
                test_data["expected_dicts"],
            ]

            # Call function under test
            remap_vars(
                test_data["files"],
                test_data["kernel_dinstrs"],
                test_data["kernel_ops"],
                MagicMock(),
            )

        # Assert
        # Verify remap_dinstrs_vars was called for each kernel with the correct arguments
        assert mock_remap_vars.call_count == 2

        # First call
        mock_remap_vars.assert_any_call(test_data["kernel_dinstrs"][0], test_data["kernel_ops"][0])

        # Second call
        mock_remap_vars.assert_any_call(test_data["kernel_dinstrs"][1], test_data["kernel_ops"][1])

        # Verify the remap_dict was set on each kernel file
        assert test_data["files"][0].remap_dict == test_data["expected_dicts"]
        assert test_data["files"][1].remap_dict == test_data["expected_dicts"]

    def test_remap_vars_with_mismatched_prefixes(self):
        """
        @brief Test remap_vars correctly handles mismatched prefixes
        """
        # Arrange
        mock_files = [MagicMock(spec=KernelInfo)]
        mock_files[0].prefix = "kernel1_pisa.tw"

        kernel_ops = [MagicMock()]
        kernel_ops[0].expected_in_kern_file_name = "different_kernel"

        kernel_dinstrs = [[MagicMock()]]

        # Act & Assert
        with pytest.raises(AssertionError, match="prefix .* does not match"):
            remap_vars(mock_files, kernel_dinstrs, kernel_ops, MagicMock())

    def test_remap_vars_with_empty_input(self):
        """
        @brief Test remap_vars with an empty list of input files
        """
        # Arrange
        kernel_files = []
        kernel_dinstrs = []
        kernel_ops = []
        verbose_stream = MagicMock()

        # Act
        # No exception should be raised for empty inputs
        remap_vars(kernel_files, kernel_dinstrs, kernel_ops, verbose_stream)

        # Assert
        # Just verifying the function completes without error

    def test_remap_vars_length_mismatch(self):
        """
        @brief Test remap_vars correctly handles mismatched lengths
        """
        # Arrange - mismatched lengths between files and ops
        kernel_files = [MagicMock(), MagicMock()]
        kernel_dinstrs = [[MagicMock()]]
        kernel_ops = [MagicMock()]

        # Act & Assert
        with pytest.raises(AssertionError, match="Number of kernels_files must match"):
            remap_vars(kernel_files, kernel_dinstrs, kernel_ops, MagicMock())

        # Arrange - mismatched lengths between dinstrs and ops
        kernel_files = [MagicMock()]
        kernel_dinstrs = [[MagicMock()], [MagicMock()]]
        kernel_ops = [MagicMock()]

        # Act & Assert
        with pytest.raises(AssertionError, match="Number of kernel_dinstrs must match"):
            remap_vars(kernel_files, kernel_dinstrs, kernel_ops, MagicMock())

    def test_initialize_memory_model_with_kernel_dinstrs(self):
        """
        @brief Test initialize_memory_model when kernel_dinstrs is provided (trace file mode)
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.hbm_size = 1024

        # Create mock kernel DInstructions
        mock_dinstrs = [MagicMock(), MagicMock()]

        # Create mock mem_meta_info
        mock_mem_info = MagicMock()

        # Create mock verbose stream
        mock_stream = MagicMock()

        # Act
        with (
            patch("assembler.common.constants.convertBytes2Words", return_value=1024 * 1024) as mock_convert,
            patch(
                "assembler.memory_model.mem_info.MemInfo.from_dinstrs",
                return_value=mock_mem_info,
            ) as mock_from_dinstrs,
            patch("linker.MemoryModel") as mock_memory_model_class,
        ):
            # Configure mock memory model
            mock_memory_model = mock_memory_model_class.return_value
            mock_memory_model.hbm.capacity = 1024 * 1024

            # Call function under test
            result = initialize_memory_model(mock_config, mock_dinstrs, mock_stream)

        # Assert
        # Verify convertBytes2Words was called with correct parameters
        mock_convert.assert_called_once_with(mock_config.hbm_size * constants.Constants.KILOBYTE)

        # Verify from_dinstrs was called with kernel_dinstrs
        mock_from_dinstrs.assert_called_once_with(mock_dinstrs)

        # Verify MemoryModel was initialized with correct parameters
        mock_memory_model_class.assert_called_once_with(1024 * 1024, mock_mem_info)

        # Verify output was written to the verbose stream
        assert mock_stream.write.call_count >= 1

        # Verify the result is the mock memory model
        assert result is mock_memory_model

    def test_initialize_memory_model_with_input_mem_file(self):
        """
        @brief Test initialize_memory_model when reading from input_mem_file (standard mode)
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.hbm_size = 2048
        mock_config.input_mem_file = "/path/to/input.mem"

        # Create mock mem_meta_info
        mock_mem_info = MagicMock()  # Create mock verbose stream
        mock_stream = MagicMock()

        # Act
        with (
            patch("assembler.common.constants.convertBytes2Words", return_value=2048 * 1024) as mock_convert,
            patch("builtins.open", mock_open()) as mock_open_file,
            patch(
                "assembler.memory_model.mem_info.MemInfo.from_file_iter",
                return_value=mock_mem_info,
            ) as mock_from_file_iter,
            patch("linker.MemoryModel") as mock_memory_model_class,
        ):
            # Configure mock memory model
            mock_memory_model = mock_memory_model_class.return_value
            mock_memory_model.hbm.capacity = 2048 * 1024

            # Call function under test
            result = initialize_memory_model(mock_config, None, mock_stream)

        # Assert
        # Verify convertBytes2Words was called with correct parameters
        mock_convert.assert_called_once_with(mock_config.hbm_size * constants.Constants.KILOBYTE)

        # Verify open was called with input_mem_file
        mock_open_file.assert_called_once_with(mock_config.input_mem_file, "r", encoding="utf-8")

        # Verify from_file_iter was called
        assert mock_from_file_iter.called

        # Verify MemoryModel was initialized with correct parameters
        mock_memory_model_class.assert_called_once_with(2048 * 1024, mock_mem_info)

        # Verify output was written to the verbose stream
        assert mock_stream.write.call_count >= 1

        # Verify the result is the mock memory model
        assert result is mock_memory_model

    def test_initialize_memory_model_with_zero_hbm_size(self):
        """
        @brief Test initialize_memory_model with hbm_size=0
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.hbm_size = 0  # Zero HBM size

        # Create mock kernel DInstructions
        mock_dinstrs = [MagicMock()]

        # Create mock mem_meta_info
        mock_mem_info = MagicMock()

        # Act
        with (
            patch("assembler.common.constants.convertBytes2Words", return_value=0) as mock_convert,
            patch(
                "assembler.memory_model.mem_info.MemInfo.from_dinstrs",
                return_value=mock_mem_info,
            ),
            patch("linker.MemoryModel") as mock_memory_model_class,
        ):
            # Call function under test
            result = initialize_memory_model(mock_config, mock_dinstrs)

        # Assert
        # Verify convertBytes2Words was called with 0
        mock_convert.assert_called_once_with(0)

        # Verify MemoryModel was initialized with hbm_capacity_words=0
        mock_memory_model_class.assert_called_once_with(0, mock_mem_info)

        # Verify the result is the mock memory model
        assert result is mock_memory_model_class.return_value
