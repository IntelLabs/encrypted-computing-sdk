# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link.py
@brief Unit tests for the he_link module
"""
import io
import argparse
from unittest.mock import patch, mock_open, MagicMock
import pytest

import he_link
from linker.kern_trace import KernelInfo


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
            KernelInfo(
                {
                    "directory": "/tmp",
                    "prefix": expected_kernel_name,  # Match the expected name pattern
                    "minst": f"{expected_kernel_name}.minst",
                    "cinst": f"{expected_kernel_name}.cinst",
                    "xinst": f"{expected_kernel_name}.xinst",
                    "mem": f"{expected_kernel_name}.mem" if using_trace_file else None,
                }
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
            "update_input_prefixes": MagicMock(
                return_value={"kernel1_pisa.tw": MagicMock()}
            ),
            "remap_vars": MagicMock(
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
            "he_link.Loader.load_dinst_kernel_from_file", mocks["load_dinst"]
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
            "linker.kern_trace.remap_dinstrs_vars", mocks["remap_dinstrs_vars"]
        ), patch(
            "he_link.update_input_prefixes", mocks["update_input_prefixes"]
        ), patch(
            "he_link.remap_vars", mocks["remap_vars"]
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
            mocks["update_input_prefixes"].assert_called_once()
            mocks["remap_vars"].assert_called_once()
            mocks["initialize_memory_model"].assert_called_once()
            assert not mocks["from_file_iter"].called
        else:
            # Assert that the normal flow was used
            assert not mocks["update_input_prefixes"].called
            assert not mocks["remap_vars"].called
            mocks["initialize_memory_model"].assert_called_once()

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
        ), patch("linker.he_link_utils.prepare_output_files"), patch(
            "linker.he_link_utils.prepare_input_files"
        ), patch(
            "assembler.common.counter.Counter.reset"
        ), patch(
            "builtins.open", mock_open()
        ), patch(
            "assembler.memory_model.mem_info.MemInfo.from_file_iter"
        ), patch(
            "linker.MemoryModel"
        ), patch(
            "linker.steps.variable_discovery.scan_variables"
        ), patch(
            "linker.steps.variable_discovery.check_unused_variables"
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

    def test_trace_file_with_missing_output_prefix(self):
        """
        @brief Test parse_args when trace_file is provided but output_prefix (always required) is missing
        """
        # Instead of manually creating a namespace with missing required arguments,
        # we'll create an argv list that's missing the required argument
        mock_argv = ["he_link.py", "--use_trace_file", "trace_file_path"]

        # Create a StringIO to capture the error output
        error_output = io.StringIO()

        # Patch sys.argv and sys.stderr
        with patch("sys.argv", mock_argv), patch("sys.stderr", error_output), patch(
            "sys.exit"
        ) as mock_exit:
            # When required args are missing, argparse will call sys.exit()
            he_link.parse_args()

            # Verify that exit was called (indicating an error)
            mock_exit.assert_called()

            # Verify the error output contains information about the missing required argument
            error_message = error_output.getvalue()
            assert "output_prefix" in error_message
            assert "required" in error_message.lower()

    def test_required_args_when_trace_file_not_set(self):
        """
        @brief Test that input_mem_file and input_prefixes are required when trace_file is not set
        """
        # Case 1: Missing input_mem_file
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="",  # Empty input_mem_file
                trace_file="",  # No trace file
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
        ), patch("argparse.ArgumentParser.error") as mock_error:
            he_link.parse_args()
            # Verify error was called for missing input_mem_file
            mock_error.assert_called_once_with(
                "the following arguments are required: -im/--input_mem_file (unless --use_trace_file is set)"
            )

        # Case 2: Missing input_prefixes
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=None,  # Missing input_prefixes
                output_prefix="output_prefix",
                input_mem_file="input.mem",
                trace_file="",  # No trace file
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
        ), patch("argparse.ArgumentParser.error") as mock_error:
            he_link.parse_args()
            # Verify error was called for missing input_prefixes
            mock_error.assert_called_once_with(
                "the following arguments are required: -ip/--input_prefixes (unless --use_trace_file is set)"
            )

    def test_ignored_args_when_trace_file_set(self):
        """
        @brief Test that input_mem_file and input_prefixes are ignored with warnings when trace_file is set
        """
        # Both input_mem_file and input_prefixes are provided but should be ignored
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],  # Will be ignored
                output_prefix="output_prefix",
                input_mem_file="input.mem",  # Will be ignored
                trace_file="trace_file_path",  # Trace file is provided
                input_dir="",
                output_dir="",
                using_trace_file=None,  # Will be computed
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ), patch("warnings.warn") as mock_warn:
            args = he_link.parse_args()

            # Verify using_trace_file is set based on trace_file
            assert args.using_trace_file is True

            # Verify warnings were issued for ignored arguments
            assert mock_warn.call_count == 2
            # Check warning messages
            warning_messages = [call.args[0] for call in mock_warn.call_args_list]
            assert any("Ignoring input_mem_file" in msg for msg in warning_messages)
            assert any("Ignoring input_prefixes" in msg for msg in warning_messages)

    def test_hbm_flags_parsing(self):
        """
        @brief Test the parsing of --hbm_size and --no_hbm flags
        """
        # Test with hbm_size set to valid value
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
                hbm_size=2048,  # Valid hbm_size
                suppress_comments=False,
                verbose=0,
            ),
        ):
            args = he_link.parse_args()
            assert args.hbm_size == 2048
            assert args.has_hbm is True

        # Test with --no_hbm flag set
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
                has_hbm=False,  # --no_hbm flag set
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ):
            args = he_link.parse_args()
            assert args.has_hbm is False

        # Test with hbm_size set to 0
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
                hbm_size=0,  # Edge case: zero
                suppress_comments=False,
                verbose=0,
            ),
        ):
            args = he_link.parse_args()
            assert args.hbm_size == 0

    def test_verbose_flag_parsing(self):
        """
        @brief Test the parsing of -v/--verbose flag at different levels
        """
        # Test with no verbose flag (default)
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
                verbose=0,  # Default level
            ),
        ):
            args = he_link.parse_args()
            assert args.verbose == 0

        # Test with single -v flag
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
                verbose=1,  # Single -v
            ),
        ):
            args = he_link.parse_args()
            assert args.verbose == 1

        # Test with double -vv flag
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
                verbose=2,  # Double -vv
            ),
        ):
            args = he_link.parse_args()
            assert args.verbose == 2

        # Test with high verbosity
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
                verbose=5,  # High verbosity
            ),
        ):
            args = he_link.parse_args()
            assert args.verbose == 5

    def test_input_dir_defaults_to_trace_file_directory(self):
        """
        @brief Test that input_dir defaults to the directory of trace_file when not specified
        """
        # Test with trace_file set but input_dir not set
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=None,
                output_prefix="output_prefix",
                input_mem_file="",
                input_dir="",  # Not specified
                trace_file="/path/to/trace_file.txt",  # Trace file with a directory path
                output_dir="",
                using_trace_file=None,  # Will be computed
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ), patch("os.path.dirname", return_value="/path/to") as mock_dirname:
            args = he_link.parse_args()

            # Verify input_dir is set to the directory of trace_file
            mock_dirname.assert_called_once_with("/path/to/trace_file.txt")
            assert args.input_dir == "/path/to"

        # Test with both trace_file and input_dir specified - input_dir should not be overwritten
        with patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=None,
                output_prefix="output_prefix",
                input_mem_file="",
                input_dir="/custom/path",  # Specified by user
                trace_file="/path/to/trace_file.txt",
                output_dir="",
                using_trace_file=None,
                mem_spec_file="",
                isa_spec_file="",
                has_hbm=True,
                hbm_size=None,
                suppress_comments=False,
                verbose=0,
            ),
        ), patch("os.path.dirname") as mock_dirname:
            args = he_link.parse_args()

            # Verify dirname was not called since input_dir was already specified
            mock_dirname.assert_not_called()
            # Input_dir should remain as specified
            assert args.input_dir == "/custom/path"
