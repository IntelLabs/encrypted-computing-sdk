# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link_utils.py
@brief Unit tests for the he_link_utils module
"""
from unittest.mock import patch, mock_open, MagicMock
import pytest

from linker.he_link_utils import (
    prepare_output_files,
    prepare_input_files,
    process_trace_file,
    process_kernel_dinstrs,
    initialize_memory_model,
    KernelFiles,
)
from assembler.common import constants


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
        with patch("os.path.dirname", return_value="/tmp"), patch(
            "pathlib.Path.mkdir"
        ), patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
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
        with patch("os.path.dirname", return_value="/tmp"), patch(
            "pathlib.Path.mkdir"
        ), patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
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

        mock_output_files = KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/output.minst",
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act
        with patch("os.path.isfile", return_value=True), patch(
            "assembler.common.makeUniquePath", side_effect=lambda x: x
        ):
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

        mock_output_files = KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/output.minst",
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=False), patch(
            "assembler.common.makeUniquePath", side_effect=lambda x: x
        ):
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
        mock_output_files = KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/input1.minst",  # Conflict
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=True), patch(
            "assembler.common.makeUniquePath", side_effect=lambda x: x
        ):
            with pytest.raises(RuntimeError):
                prepare_input_files(mock_config, mock_output_files)

    def test_process_trace_file(self):
        """
        @brief Test process_trace_file correctly processes a trace file and returns kernel operations dictionary
        """
        # Arrange
        mock_trace_file = "/path/to/trace_file.txt"

        # Create mock kernel ops with expected_in_kern_file_name attribute
        mock_kernel_op1 = MagicMock()
        mock_kernel_op1.expected_in_kern_file_name = "kernel1"

        mock_kernel_op2 = MagicMock()
        mock_kernel_op2.expected_in_kern_file_name = "kernel2"

        mock_kernel_ops = [mock_kernel_op1, mock_kernel_op2]

        # Act
        with patch("linker.he_link_utils.TraceInfo") as mock_trace_info_class:
            # Configure the mock TraceInfo instance
            mock_trace_info = mock_trace_info_class.return_value
            mock_trace_info.parse_kernel_ops.return_value = mock_kernel_ops

            # Call the function under test
            result = process_trace_file(mock_trace_file)

        # Assert
        # Verify TraceInfo was constructed with the trace file
        mock_trace_info_class.assert_called_once_with(mock_trace_file)

        # Verify parse_kernel_ops was called
        mock_trace_info.parse_kernel_ops.assert_called_once()

        # Verify the result is a dictionary with the expected keys
        assert len(result) == 2
        assert "kernel1_pisa.tw" in result
        assert "kernel2_pisa.tw" in result

        # Verify the dictionary values are the kernel ops
        assert result["kernel1_pisa.tw"] is mock_kernel_op1
        assert result["kernel2_pisa.tw"] is mock_kernel_op2

    def test_process_trace_file_with_empty_kernel_ops(self):
        """
        @brief Test process_trace_file correctly handles empty kernel operations
        """
        # Arrange
        mock_trace_file = "/path/to/trace_file.txt"
        mock_kernel_ops = []  # Empty list of kernel ops

        # Act
        with patch("linker.he_link_utils.TraceInfo") as mock_trace_info_class:
            # Configure the mock TraceInfo instance
            mock_trace_info = mock_trace_info_class.return_value
            mock_trace_info.parse_kernel_ops.return_value = mock_kernel_ops

            # Call the function under test
            result = process_trace_file(mock_trace_file)

        # Assert
        # Verify the result is an empty dictionary
        assert isinstance(result, dict)
        assert len(result) == 0

        # Verify TraceInfo was constructed with the trace file
        mock_trace_info_class.assert_called_once_with(mock_trace_file)

        # Verify parse_kernel_ops was called
        mock_trace_info.parse_kernel_ops.assert_called_once()

    def _create_kernel_test_data(self):
        """
        @brief Helper method to create test data for process_kernel_dinstrs tests
        @return Tuple containing test data: (kernels_files, kernel_ops_dict, test_dinstrs, expected_dicts)
        """
        # Create mock kernel files
        mock_files = []
        for i in range(1, 3):
            kernel_file = MagicMock(spec=KernelFiles)
            kernel_file.prefix = f"kernel{i}_pisa.tw"
            kernel_file.mem = f"/path/to/kernel{i}.mem"
            mock_files.append(kernel_file)

        # Create mock kernel operations
        kernel_ops = {}
        for i in range(1, 3):
            kernel_ops[f"kernel{i}_pisa.tw"] = MagicMock()

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
            "kernel1_pisa.tw": {"var1": "mapped_var1"},
            "kernel2_pisa.tw": {"var2": "mapped_var2", "var3": "mapped_var3"},
        }

        # Pack test data
        test_data = {
            "files": mock_files,
            "ops_dict": kernel_ops,
            "dinstrs": dinstrs,
            "kernel_dinstrs": kernel_dinstrs,
            "expected_dicts": expected_dicts,
            "joined_dinstrs": dinstrs,  # All dinstrs joined
        }

        return test_data

    def test_process_kernel_dinstrs_with_multiple_kernels(self):
        """
        @brief Test process_kernel_dinstrs with multiple input kernel files
        """
        # Arrange - Get test data from helper method
        test_data = self._create_kernel_test_data()

        # Act
        with patch(
            "linker.loader.load_dinst_kernel_from_file"
        ) as mock_load_dinst, patch(
            "linker.he_link_utils.remap_dinstrs_vars"
        ) as mock_remap_vars, patch(
            "linker.steps.program_linker.LinkedProgram.join_dinst_kernels"
        ) as mock_join_kernels:

            # Configure mocks
            mock_load_dinst.side_effect = test_data["kernel_dinstrs"]
            mock_remap_vars.side_effect = list(test_data["expected_dicts"].values())
            mock_join_kernels.return_value = test_data["joined_dinstrs"]

            # Call function under test
            result = process_kernel_dinstrs(
                test_data["files"], test_data["ops_dict"], MagicMock()
            )

        # Assert
        # Verify load_dinst_kernel_from_file was called for each input file
        assert mock_load_dinst.call_count == 2
        mock_load_dinst.assert_any_call(test_data["files"][0].mem)
        mock_load_dinst.assert_any_call(test_data["files"][1].mem)

        # Verify remap_dinstrs_vars was called for each kernel
        assert mock_remap_vars.call_count == 2
        mock_remap_vars.assert_any_call(
            test_data["kernel_dinstrs"][0],
            test_data["ops_dict"][test_data["files"][0].prefix],
        )
        mock_remap_vars.assert_any_call(
            test_data["kernel_dinstrs"][1],
            test_data["ops_dict"][test_data["files"][1].prefix],
        )

        # Verify join_dinst_kernels was called once with all kernel dinstrs
        mock_join_kernels.assert_called_once()

        # Unpack and verify results
        result_dinstrs, result_remap_dicts = result
        assert result_dinstrs == test_data["joined_dinstrs"]
        assert result_remap_dicts == test_data["expected_dicts"]

    def test_process_kernel_dinstrs_with_empty_input(self):
        """
        @brief Test process_kernel_dinstrs with an empty list of input files
        """
        # Arrange
        input_files = []
        kernel_ops_dict = {}

        # Act
        with patch(
            "linker.steps.program_linker.LinkedProgram.join_dinst_kernels"
        ) as mock_join_kernels:
            mock_join_kernels.return_value = []

            # Call function under test
            result_dinstrs, result_remap_dicts = process_kernel_dinstrs(
                input_files, kernel_ops_dict, MagicMock()
            )

        # Assert
        # Verify join_dinst_kernels was called once with an empty list
        mock_join_kernels.assert_called_once_with([])

        # Verify the returned values
        assert not result_dinstrs
        assert not result_remap_dicts

    def test_process_kernel_dinstrs_handles_exceptions(self):
        """
        @brief Test process_kernel_dinstrs correctly propagates exceptions
        """
        # Arrange
        mock_kernel_file = MagicMock(spec=KernelFiles)
        mock_kernel_file.prefix = "kernel1_pisa.tw"
        mock_kernel_file.mem = "/path/to/kernel1.mem"

        input_files = [mock_kernel_file]

        mock_kernel_op = MagicMock()
        kernel_ops_dict = {"kernel1_pisa.tw": mock_kernel_op}

        # Act & Assert
        # Test with load_dinst_kernel_from_file raising exception
        with patch(
            "linker.loader.load_dinst_kernel_from_file",
            side_effect=FileNotFoundError("File not found"),
        ), pytest.raises(FileNotFoundError, match="File not found"):
            process_kernel_dinstrs(input_files, kernel_ops_dict, MagicMock())

        # Test with remap_dinstrs_vars raising exception
        with patch(
            "linker.loader.load_dinst_kernel_from_file", return_value=[MagicMock()]
        ), patch(
            "linker.he_link_utils.remap_dinstrs_vars",
            side_effect=KeyError("Missing key"),
        ), pytest.raises(
            KeyError, match="Missing key"
        ):
            process_kernel_dinstrs(input_files, kernel_ops_dict, MagicMock())

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
        with patch(
            "assembler.common.constants.convertBytes2Words", return_value=1024 * 1024
        ) as mock_convert, patch(
            "assembler.memory_model.mem_info.MemInfo.from_dinstrs",
            return_value=mock_mem_info,
        ) as mock_from_dinstrs, patch(
            "linker.MemoryModel"
        ) as mock_memory_model_class:

            # Configure mock memory model
            mock_memory_model = mock_memory_model_class.return_value
            mock_memory_model.hbm.capacity = 1024 * 1024

            # Call function under test
            result = initialize_memory_model(mock_config, mock_dinstrs, mock_stream)

        # Assert
        # Verify convertBytes2Words was called with correct parameters
        mock_convert.assert_called_once_with(
            mock_config.hbm_size * constants.Constants.KILOBYTE
        )

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
        mock_mem_info = MagicMock()

        # Create mock verbose stream
        mock_stream = MagicMock()

        # Act
        with patch(
            "assembler.common.constants.convertBytes2Words", return_value=2048 * 1024
        ) as mock_convert, patch("builtins.open", mock_open()) as mock_open_file, patch(
            "assembler.memory_model.mem_info.MemInfo.from_file_iter",
            return_value=mock_mem_info,
        ) as mock_from_file_iter, patch(
            "linker.MemoryModel"
        ) as mock_memory_model_class:

            # Configure mock memory model
            mock_memory_model = mock_memory_model_class.return_value
            mock_memory_model.hbm.capacity = 2048 * 1024

            # Call function under test
            result = initialize_memory_model(mock_config, None, mock_stream)

        # Assert
        # Verify convertBytes2Words was called with correct parameters
        mock_convert.assert_called_once_with(
            mock_config.hbm_size * constants.Constants.KILOBYTE
        )

        # Verify open was called with input_mem_file
        mock_open_file.assert_called_once_with(
            mock_config.input_mem_file, "r", encoding="utf-8"
        )

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
        with patch(
            "assembler.common.constants.convertBytes2Words", return_value=0
        ) as mock_convert, patch(
            "assembler.memory_model.mem_info.MemInfo.from_dinstrs",
            return_value=mock_mem_info,
        ), patch(
            "linker.MemoryModel"
        ) as mock_memory_model_class:

            # Call function under test
            result = initialize_memory_model(mock_config, mock_dinstrs)

        # Assert
        # Verify convertBytes2Words was called with 0
        mock_convert.assert_called_once_with(0)

        # Verify MemoryModel was initialized with hbm_capacity_words=0
        mock_memory_model_class.assert_called_once_with(0, mock_mem_info)

        # Verify the result is the mock memory model
        assert result is mock_memory_model_class.return_value
