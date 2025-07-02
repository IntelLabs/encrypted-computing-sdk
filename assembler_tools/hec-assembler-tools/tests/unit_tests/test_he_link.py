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
            "find_mem_files": False,
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
        assert config.find_mem_files is False

    def test_init_with_missing_required_param(self):
        """
        @brief Test initialization with missing required parameters
        """
        # Arrange
        kwargs = {
            "output_prefix": "output_prefix",
            "input_mem_file": "input.mem",
            # Missing input_prefixes
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
        assert config.find_mem_files is False


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
        kernel_files = he_link.KernelFiles(
            prefix="prefix",
            minst="prefix.minst",
            cinst="prefix.cinst",
            xinst="prefix.xinst",
            mem="prefix.mem",
        )

        # Assert
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
        kernel_files = he_link.KernelFiles(
            prefix="prefix",
            minst="prefix.minst",
            cinst="prefix.cinst",
            xinst="prefix.xinst",
        )

        # Assert
        assert kernel_files.prefix == "prefix"
        assert kernel_files.minst == "prefix.minst"
        assert kernel_files.cinst == "prefix.cinst"
        assert kernel_files.xinst == "prefix.xinst"
        assert kernel_files.mem is None


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
        mock_config.find_mem_files = False

        # Act
        with patch("os.path.dirname", return_value="/tmp"), patch(
            "pathlib.Path.mkdir"
        ), patch("he_link.makeUniquePath", side_effect=lambda x: x):
            result = he_link.prepare_output_files(mock_config)

        # Assert
        assert result.prefix == "/tmp/output"
        assert result.minst == "/tmp/output.minst"
        assert result.cinst == "/tmp/output.cinst"
        assert result.xinst == "/tmp/output.xinst"
        assert result.mem is None

    def test_prepare_output_files_with_mem(self):
        """
        @brief Test prepare_output_files with find_mem_files=True
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.output_dir = "/tmp"
        mock_config.output_prefix = "output"
        mock_config.find_mem_files = True

        # Act
        with patch("os.path.dirname", return_value="/tmp"), patch(
            "pathlib.Path.mkdir"
        ), patch("he_link.makeUniquePath", side_effect=lambda x: x):
            result = he_link.prepare_output_files(mock_config)

        # Assert
        assert result.prefix == "/tmp/output"
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
        mock_config.input_prefixes = ["/tmp/input1", "/tmp/input2"]
        mock_config.find_mem_files = False

        mock_output_files = he_link.KernelFiles(
            prefix="/tmp/output",
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
        assert result[0].prefix == "/tmp/input1"
        assert result[0].minst == "/tmp/input1.minst"
        assert result[0].cinst == "/tmp/input1.cinst"
        assert result[0].xinst == "/tmp/input1.xinst"
        assert result[0].mem is None
        assert result[1].prefix == "/tmp/input2"

    def test_prepare_input_files_file_not_found(self):
        """
        @brief Test prepare_input_files when a file doesn't exist
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.input_prefixes = ["/tmp/input1"]
        mock_config.find_mem_files = False

        mock_output_files = he_link.KernelFiles(
            prefix="/tmp/output",
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
        mock_config.input_prefixes = ["/tmp/input1"]
        mock_config.find_mem_files = False

        # Output file matching an input file
        mock_output_files = he_link.KernelFiles(
            prefix="/tmp/output",
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

    @pytest.mark.parametrize("has_hbm", [True, False])
    def test_scan_variables(self, has_hbm):
        """
        @brief Test scan_variables function with and without HBM
        @param has_hbm Boolean indicating whether HBM is enabled
        """
        # Arrange
        GlobalConfig.hasHBM = has_hbm
        mock_mem_model = MagicMock()
        mock_verbose = MagicMock()

        input_files = [
            he_link.KernelFiles(
                prefix="/tmp/input1",
                minst="/tmp/input1.minst",
                cinst="/tmp/input1.cinst",
                xinst="/tmp/input1.xinst",
            )
        ]

        # Act
        with patch("linker.loader.load_minst_kernel_from_file", return_value=[]), patch(
            "linker.loader.load_cinst_kernel_from_file", return_value=[]
        ), patch(
            "linker.steps.variable_discovery.discoverVariables",
            return_value=["var1", "var2"],
        ), patch(
            "linker.steps.variable_discovery.discoverVariablesSPAD",
            return_value=["var1", "var2"],
        ):
            he_link.scan_variables(input_files, mock_mem_model, mock_verbose)

        # Assert
        if has_hbm:
            assert mock_mem_model.addVariable.call_count == 2
        else:
            assert mock_mem_model.addVariable.call_count == 2

    def test_check_unused_variables(self):
        """
        @brief Test check_unused_variables function
        """
        # Arrange
        GlobalConfig.hasHBM = True
        mock_mem_model = MagicMock()
        mock_mem_model.mem_info_vars = {"var1": MagicMock(), "var2": MagicMock()}
        mock_mem_model.variables = {"var1"}
        mock_mem_model.mem_info_meta = {}

        # Act & Assert
        with pytest.raises(RuntimeError):
            he_link.check_unused_variables(mock_mem_model)

    def test_link_kernels(self):
        """
        @brief Test link_kernels function
        """
        # Arrange
        input_files = [
            he_link.KernelFiles(
                prefix="/tmp/input1",
                minst="/tmp/input1.minst",
                cinst="/tmp/input1.cinst",
                xinst="/tmp/input1.xinst",
            )
        ]

        output_files = he_link.KernelFiles(
            prefix="/tmp/output",
            minst="/tmp/output.minst",
            cinst="/tmp/output.cinst",
            xinst="/tmp/output.xinst",
        )

        mock_mem_model = MagicMock()
        mock_verbose = MagicMock()

        # Act
        with patch("builtins.open", mock_open()), patch(
            "linker.loader.load_minst_kernel_from_file", return_value=[]
        ), patch("linker.loader.load_cinst_kernel_from_file", return_value=[]), patch(
            "linker.loader.load_xinst_kernel_from_file", return_value=[]
        ), patch(
            "linker.steps.program_linker.LinkedProgram"
        ) as mock_linked_program:
            he_link.link_kernels(
                input_files, output_files, mock_mem_model, mock_verbose
            )

        # Assert
        mock_linked_program.assert_called_once()
        instance = mock_linked_program.return_value
        assert instance.link_kernel.call_count == 1
        assert instance.close.call_count == 1


class TestMainFunction:
    """
    @class TestMainFunction
    @brief Test cases for the main function
    """

    @pytest.mark.parametrize("find_mem_files", [True, False])
    def test_main(self, find_mem_files):
        """
        @brief Test main function with find_mem_files=True
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.find_mem_files = find_mem_files
        mock_config.has_hbm = True
        mock_config.hbm_size = 1024
        mock_config.suppress_comments = False
        mock_config.use_xinstfetch = False

        mock_verbose = MagicMock()

        # Act
        with patch(
            "assembler.common.constants.convertBytes2Words", return_value=1024
        ), patch("he_link.prepare_output_files") as mock_prepare_output, patch(
            "he_link.prepare_input_files"
        ) as mock_prepare_input, patch(
            "assembler.common.counter.Counter.reset"
        ), patch(
            "linker.loader.load_dinst_kernel_from_file", return_value=["1", "2"]
        ) as mock_load_dinst_kernel_from_file, patch(
            "linker.instructions.BaseInstruction.dump_instructions_to_file"
        ) as mock_dump_instructions, patch(
            "linker.steps.program_linker.LinkedProgram.join_dinst_kernels",
            return_value=[],
        ) as mock_join_dinst_kernels, patch(
            "assembler.memory_model.mem_info.MemInfo.from_dinstrs"
        ) as mock_from_dinstrs, patch(
            "assembler.memory_model.mem_info.MemInfo.from_file_iter"
        ) as mock_from_file_iter, patch(
            "linker.MemoryModel"
        ), patch(
            "he_link.scan_variables"
        ) as mock_scan_variables, patch(
            "he_link.check_unused_variables"
        ) as mock_check_unused_variables, patch(
            "he_link.link_kernels"
        ) as mock_link_kernels, patch(
            "he_link.BaseInstruction.dump_instructions_to_file"
        ) as mock_dump_instructions:

            mock_prepare_input.return_value = [
                he_link.KernelFiles(
                    prefix="prefix1",
                    minst="prefix1.minst",
                    cinst="prefix1.cinst",
                    xinst="prefix1.xinst",
                    mem=None,
                ),
                he_link.KernelFiles(
                    prefix="prefix2",
                    minst="prefix2.minst",
                    cinst="prefix2.cinst",
                    xinst="prefix2.xinst",
                    mem=None,
                ),
            ]
            he_link.main(mock_config, mock_verbose)

        # Assert pipeline is run as expected
        mock_prepare_output.assert_called_once()
        mock_prepare_input.assert_called_once()
        mock_scan_variables.assert_called_once()
        mock_check_unused_variables.assert_called_once()
        mock_link_kernels.assert_called_once()

        if find_mem_files:
            # Should use from_dinstrs, not from_file_iter
            assert mock_from_dinstrs.called
            assert mock_load_dinst_kernel_from_file.called
            assert mock_join_dinst_kernels.called
            assert mock_dump_instructions.called

            assert not mock_from_file_iter.called
        else:
            # Should use from_file_iter, not from_dinstrs
            assert mock_from_file_iter.called
            assert not mock_from_dinstrs.called

    def test_warning_on_use_xinstfetch(self):
        """
        @brief Test warning is issued when use_xinstfetch is True
        """
        # Arrange
        mock_config = MagicMock()
        mock_config.find_mem_files = False
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
            "he_link.link_kernels"
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
        # Arrange
        test_args = [
            "program",
            "input_prefix",
            "-o",
            "output_prefix",
            "-im",
            "input.mem",
        ]

        # Act
        with patch("sys.argv", test_args), patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="input.mem",
                output_dir="",
                find_mem_files=False,
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
        assert args.find_mem_files is False

    def test_parse_args_find_mem_files(self):
        """
        @brief Test parse_args with find_mem_files flag
        """
        # Arrange
        test_args = [
            "program",
            "input_prefix",
            "-o",
            "output_prefix",
            "--find_mem_files",
        ]

        # Act
        with patch("sys.argv", test_args), patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="",
                output_dir="",
                find_mem_files=True,
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
        assert args.input_mem_file == ""
        assert args.find_mem_files is True

    def test_missing_input_mem_file(self):
        """
        @brief Test parse_args with missing input_mem_file when find_mem_files is False
        """
        # Arrange
        test_args = ["program", "input_prefix", "-o", "output_prefix"]

        # Act & Assert
        with patch("sys.argv", test_args), patch(
            "argparse.ArgumentParser.parse_args",
            return_value=argparse.Namespace(
                input_prefixes=["input_prefix"],
                output_prefix="output_prefix",
                input_mem_file="",
                output_dir="",
                find_mem_files=False,
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
