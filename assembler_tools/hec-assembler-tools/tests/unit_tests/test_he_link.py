# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link.py
@brief Unit tests for the he_link module
"""

import os
import argparse
from unittest.mock import patch, mock_open, MagicMock, PropertyMock
import pytest

import he_link
from assembler.common.config import GlobalConfig


class TestLinkerRunConfig:
    """
    @class TestLinkerRunConfig
    @brief Test cases for the LinkerRunConfig class
    """

    def test_init_with_valid_params(self):
        """
        @brief Test initialization with valid parameters
        """
        # Arrange
        kwargs = {
            "input_prefixes": ["prefix1", "prefix2"],
            "output_prefix": "output_prefix",
            "input_mem_file": "input.mem",
            "output_dir": "/tmp",
            "has_hbm": True,
            "hbm_size": 1024,
            "suppress_comments": False,
            "use_xinstfetch": False,
            "using_trace_file": False,
        }

        # Act
        with patch("he_link.makeUniquePath", side_effect=lambda x: x):
            config = he_link.LinkerRunConfig(**kwargs)

        # Assert
        assert config.input_prefixes == ["prefix1", "prefix2"]
        assert config.output_prefix == "output_prefix"
        assert config.input_mem_file == "input.mem"
        assert config.output_dir == "/tmp"
        assert config.has_hbm is True
        assert config.hbm_size == 1024
        assert config.suppress_comments is False
        assert config.use_xinstfetch is False
        assert config.using_trace_file is False

    def test_init_with_missing_required_param(self):
        """
        @brief Test initialization with missing required parameters
        """
        # Arrange
        kwargs = {
            "input_prefixes": ["prefix1"],
            "input_mem_file": "input.mem",
            "output_dir": "/tmp",
            # Missing output_prefixes
        }

        # Act & Assert
        with pytest.raises(TypeError):
            he_link.LinkerRunConfig(**kwargs)

    def test_as_dict(self):
        """
        @brief Test the as_dict method returns a proper dictionary
        """
        # Arrange
        kwargs = {
            "input_prefixes": ["prefix1"],
            "output_prefix": "output_prefix",
            "input_mem_file": "input.mem",
            "output_dir": "/tmp",
            "has_hbm": True,
            "hbm_size": 1024,
        }

        # Act
        with patch("he_link.makeUniquePath", side_effect=lambda x: x):
            config = he_link.LinkerRunConfig(**kwargs)
            result = config.as_dict()

        # Assert Keys
        assert isinstance(result, dict)
        assert "input_prefixes" in result
        assert "output_prefix" in result
        assert "input_mem_file" in result
        assert "output_dir" in result
        assert "has_hbm" in result
        assert "hbm_size" in result

        # Assert values
        assert result["input_prefixes"] == ["prefix1"]
        assert result["output_prefix"] == "output_prefix"
        assert result["input_mem_file"] == "input.mem"
        assert result["output_dir"] == "/tmp"
        assert result["has_hbm"] is True
        assert result["hbm_size"] == 1024

    def test_str_representation(self):
        """
        @brief Test the string representation of the configuration
        """
        # Arrange
        kwargs = {
            "input_prefixes": ["prefix1"],
            "output_prefix": "output_prefix",
            "input_mem_file": "input.mem",
        }

        # Act
        with patch("he_link.makeUniquePath", side_effect=lambda x: x):
            config = he_link.LinkerRunConfig(**kwargs)
            result = str(config)

        # Assert params
        assert "input_prefixes" in result
        assert "output_prefix" in result
        assert "input_mem_file" in result
        # Assert values
        assert "prefix1" in result
        assert "output_prefix" in result
        assert "input.mem" in result

    def test_init_for_default_params(self):
        """
        @brief Test initialization with default parameters
        """

        # Arrange
        kwargs = {"input_prefixes": ["prefix1"], "output_prefix": ""}

        # Reset the class-level config so the patch will take effect
        he_link.RunConfig.reset_class_state()

        # Act
        with patch("he_link.makeUniquePath", side_effect=lambda x: x), patch.object(
            he_link.RunConfig, "DEFAULT_HBM_SIZE_KB", new_callable=PropertyMock
        ) as mock_hbm_size, patch.object(
            GlobalConfig, "suppress_comments", new_callable=PropertyMock
        ) as mock_suppress_comments, patch.object(
            GlobalConfig, "useXInstFetch", new_callable=PropertyMock
        ) as mock_use_xinstfetch:

            # Mock the default HBM size
            mock_suppress_comments.return_value = False
            mock_use_xinstfetch.return_value = False
            mock_hbm_size.return_value = 1024
            config = he_link.LinkerRunConfig(**kwargs)

        # Assert
        assert config.output_prefix == ""
        assert config.input_mem_file == ""
        assert config.output_dir == os.getcwd()
        assert config.has_hbm is True
        assert config.hbm_size == 1024
        assert config.suppress_comments is False
        assert config.use_xinstfetch is False
        assert config.using_trace_file is False


class TestHelperFunctions:
    """
    @class TestHelperFunctions
    @brief Test cases for helper functions in he_link
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
        ), patch("he_link.makeUniquePath", side_effect=lambda x: x):
            result = he_link.prepare_output_files(mock_config)

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
        ), patch("he_link.makeUniquePath", side_effect=lambda x: x):
            result = he_link.prepare_output_files(mock_config)

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

        mock_output_files = he_link.KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/output.minst",
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act
        with patch("os.path.isfile", return_value=True), patch(
            "he_link.makeUniquePath", side_effect=lambda x: x
        ):
            result = he_link.prepare_input_files(mock_config, mock_output_files)

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

        mock_output_files = he_link.KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/output.minst",
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=False), patch(
            "he_link.makeUniquePath", side_effect=lambda x: x
        ):
            with pytest.raises(FileNotFoundError):
                he_link.prepare_input_files(mock_config, mock_output_files)

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
        mock_output_files = he_link.KernelFiles(
            directory="/tmp",
            prefix="output",
            minst="/tmp/input1.minst",  # Conflict
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        # Act & Assert
        with patch("os.path.isfile", return_value=True), patch(
            "he_link.makeUniquePath", side_effect=lambda x: x
        ):
            with pytest.raises(RuntimeError):
                he_link.prepare_input_files(mock_config, mock_output_files)


class TestMainFunction:
    """
    @class TestMainFunction
    @brief Test cases for the main function
    """

    @pytest.mark.parametrize("using_trace_file", [True, False])
    def test_main(self, using_trace_file):
        """
        @brief Test main function with and without using_trace_file
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.using_trace_file = using_trace_file
        mock_config.has_hbm = True
        mock_config.hbm_size = 1024
        mock_config.suppress_comments = False
        mock_config.use_xinstfetch = False

        # The expected kernel name pattern from parse_kernel_ops
        expected_kernel_name = "kernel1_pisa.tw"

        # Setup input files with conditional mem files - ensure prefix matches expected pattern
        input_files = [
            he_link.KernelFiles(
                directory="/tmp",
                prefix=expected_kernel_name,  # Match the expected name pattern
                minst=f"{expected_kernel_name}.minst",
                cinst=f"{expected_kernel_name}.cinst",
                xinst=f"{expected_kernel_name}.xinst",
                mem=f"{expected_kernel_name}.mem" if using_trace_file else None,
            ),
        ]

        # Create mock DInstructions with proper .var attributes
        mock_dinstr1 = MagicMock()
        mock_dinstr1.var = "ct0_data"
        mock_dinstr2 = MagicMock()
        mock_dinstr2.var = "pt1_result"

        # Create a dictionary of mocks to reduce the number of local variables
        mocks = {
            "prepare_output": MagicMock(),
            "prepare_input": MagicMock(return_value=input_files),
            "scan_variables": MagicMock(),
            "check_unused_variables": MagicMock(),
            "link_kernels": MagicMock(),
            "from_dinstrs": MagicMock(),
            "from_file_iter": MagicMock(),
            "load_dinst": MagicMock(
                return_value=[mock_dinstr1, mock_dinstr2]
            ),  # Return mock DInstructions
            "join_dinst": MagicMock(return_value=[]),
            "dump_instructions": MagicMock(),
            "remap_dinstrs_vars": MagicMock(return_value={"old_var": "new_var"}),
            "process_trace_file": MagicMock(
                return_value={"kernel1_pisa.tw": MagicMock()}
            ),
            "process_kernel_dinstrs": MagicMock(
                return_value=([mock_dinstr1, mock_dinstr2], {"key": "value"})
            ),
            "initialize_memory_model": MagicMock(),
            # Return a kernel_op with expected_in_kern_file_name that will match our input file prefix
            "parse_kernel_ops": MagicMock(
                return_value=[
                    MagicMock(
                        expected_in_kern_file_name="kernel1",
                        kern_vars=[
                            MagicMock(label="input"),
                            MagicMock(label="output"),
                        ],  # Add mock kern_vars
                    )
                ]
            ),
        }

        # Add trace_file property to mock_config
        mock_config.trace_file = "mock_trace.txt" if using_trace_file else ""

        # Act
        with patch(
            "assembler.common.constants.convertBytes2Words", return_value=1024
        ), patch("he_link.prepare_output_files", mocks["prepare_output"]), patch(
            "he_link.prepare_input_files", mocks["prepare_input"]
        ), patch(
            "assembler.common.counter.Counter.reset"
        ), patch(
            "linker.loader.load_dinst_kernel_from_file", mocks["load_dinst"]
        ), patch(
            "linker.instructions.BaseInstruction.dump_instructions_to_file",
            mocks["dump_instructions"],
        ), patch(
            "linker.steps.program_linker.LinkedProgram.join_dinst_kernels",
            mocks["join_dinst"],
        ), patch(
            "assembler.memory_model.mem_info.MemInfo.from_dinstrs",
            mocks["from_dinstrs"],
        ), patch(
            "assembler.memory_model.mem_info.MemInfo.from_file_iter",
            mocks["from_file_iter"],
        ), patch(
            "linker.MemoryModel"
        ), patch(
            "he_link.scan_variables", mocks["scan_variables"]
        ), patch(
            "he_link.check_unused_variables", mocks["check_unused_variables"]
        ), patch(
            "linker.kern_trace.TraceInfo.parse_kernel_ops", mocks["parse_kernel_ops"]
        ), patch(
            "os.path.isfile",
            return_value=True,  # Make all file existence checks return True
        ), patch(
            "linker.steps.program_linker.LinkedProgram.link_kernels_to_files",
            mocks["link_kernels"],
        ), patch(
            "he_link.remap_dinstrs_vars", mocks["remap_dinstrs_vars"]
        ), patch(
            "he_link.process_trace_file", mocks["process_trace_file"]
        ), patch(
            "he_link.process_kernel_dinstrs", mocks["process_kernel_dinstrs"]
        ), patch(
            "he_link.initialize_memory_model", mocks["initialize_memory_model"]
        ):

            # Run the main function with all patches in place
            he_link.main(mock_config, MagicMock())

        # Assert pipeline is run as expected
        mocks["prepare_output"].assert_called_once()
        mocks["prepare_input"].assert_called_once()
        mocks["scan_variables"].assert_called_once()
        mocks["check_unused_variables"].assert_called_once()
        mocks["link_kernels"].assert_called_once()

        if using_trace_file:
            # Assert that the trace processing flow was used
            mocks["process_trace_file"].assert_called_once()
            mocks["process_kernel_dinstrs"].assert_called_once()
            mocks["initialize_memory_model"].assert_called_once()

            # With the new refactoring, from_dinstrs would be called inside initialize_memory_model
            # which we're now mocking entirely, so we should check that initialize_memory_model
            # was called with the expected arguments instead
            assert mocks["initialize_memory_model"].call_args[0][0] == mock_config
            assert mocks["initialize_memory_model"].call_args[0][1] is not None

            assert not mocks["from_file_iter"].called
        else:
            # Assert that the normal flow was used
            assert not mocks["process_trace_file"].called
            assert not mocks["process_kernel_dinstrs"].called
            mocks["initialize_memory_model"].assert_called_once()

            # Check that initialize_memory_model was called with None for kernel_dinstrs
            assert mocks["initialize_memory_model"].call_args[0][0] == mock_config
            assert mocks["initialize_memory_model"].call_args[0][1] is None

    def test_warning_on_use_xinstfetch(self):
        """
        @brief Test warning is issued when use_xinstfetch is True
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.using_trace_file = False
        mock_config.has_hbm = True
        mock_config.hbm_size = 1024
        mock_config.suppress_comments = False
        mock_config.use_xinstfetch = True  # Should trigger warning
        mock_config.input_mem_file = "input.mem"

        # Act & Assert
        with patch("warnings.warn") as mock_warn, patch(
            "assembler.common.constants.convertBytes2Words", return_value=1024
        ), patch("he_link.prepare_output_files"), patch(
            "he_link.prepare_input_files"
        ), patch(
            "assembler.common.counter.Counter.reset"
        ), patch(
            "builtins.open", mock_open()
        ), patch(
            "assembler.memory_model.mem_info.MemInfo.from_file_iter"
        ), patch(
            "linker.MemoryModel"
        ), patch(
            "he_link.scan_variables"
        ), patch(
            "he_link.check_unused_variables"
        ), patch(
            "linker.steps.program_linker.LinkedProgram.link_kernels_to_files"
        ):
            he_link.main(mock_config, None)
            mock_warn.assert_called_once()


class TestParseArgs:
    """
    @class TestParseArgs
    @brief Test cases for the parse_args function
    """

    def test_parse_args_minimal(self):
        """
        @brief Test parse_args with minimal arguments
        """
        # Act - Mock the return value of parse_args directly
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="input.mem",
                trace_file="",
                input_dir="",
                output_dir="",
                using_trace_file=False,
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ):
            args = he_link.parse_args()

        # Assert
        assert args.input_prefixes == ["input_prefix"]
        assert args.output_prefix == "output_prefix"
        assert args.input_mem_file == "input.mem"
        assert args.using_trace_file is False

    def test_parse_args_using_trace_file(self):
        """
        @brief Test parse_args with using_trace_file flag
        """
        # Act - Mock the return value of parse_args directly
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=None,
                output_prefix="output_prefix",
                input_mem_file="",
                input_dir="",
                trace_file="trace_file_path",
                output_dir="",
                using_trace_file=None,  # This should be computed by parse_args function
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ):
            args = he_link.parse_args()

        # Assert
        assert args.output_prefix == "output_prefix"
        assert args.trace_file == "trace_file_path"
        assert args.using_trace_file is True  # Should be computed from trace_file

    def test_missing_input_mem_file(self):
        """
        @brief Test parse_args with missing input_mem_file when using_trace_file is False
        """
        # Act & Assert - Mock the return value and test error handling
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="",
                input_dir="",
                output_dir="",
                trace_file="",
                using_trace_file=False,
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ), patch("argparse.ArgumentParser.error") as mock_error:
            he_link.parse_args()
            mock_error.assert_called_once()
