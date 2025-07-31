# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_linker_run_config.py
@brief Unit tests for the LinkerRunConfig class
"""

import os
from unittest.mock import PropertyMock, patch

import pytest
from assembler.common.config import GlobalConfig
from assembler.common.run_config import RunConfig
from linker.linker_run_config import LinkerRunConfig


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
        with patch("linker.linker_run_config.makeUniquePath", side_effect=lambda x: x):
            config = LinkerRunConfig(**kwargs)

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
            LinkerRunConfig(**kwargs)

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
        with patch("linker.linker_run_config.makeUniquePath", side_effect=lambda x: x):
            config = LinkerRunConfig(**kwargs)
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
        with patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
            config = LinkerRunConfig(**kwargs)
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
        RunConfig.reset_class_state()

        # Act
        with (
            patch("assembler.common.makeUniquePath", side_effect=lambda x: x),
            patch.object(RunConfig, "DEFAULT_HBM_SIZE_KB", new_callable=PropertyMock) as mock_hbm_size,
            patch.object(GlobalConfig, "suppress_comments", new_callable=PropertyMock) as mock_suppress_comments,
            patch.object(GlobalConfig, "useXInstFetch", new_callable=PropertyMock) as mock_use_xinstfetch,
        ):
            # Mock the default HBM size
            mock_suppress_comments.return_value = False
            mock_use_xinstfetch.return_value = False
            mock_hbm_size.return_value = 1024
            config = LinkerRunConfig(**kwargs)

        # Assert
        assert config.output_prefix == ""
        assert config.input_mem_file == ""
        assert config.output_dir == os.getcwd()
        assert config.has_hbm is True
        assert config.hbm_size == 1024
        assert config.suppress_comments is False
        assert config.use_xinstfetch is False
        assert config.using_trace_file is False

    def test_init_with_invalid_param_values(self):
        """
        @brief Test initialization with invalid parameter values
        """
        # Arrange
        base_kwargs = {
            "input_prefixes": ["prefix1"],
            "output_prefix": "output_prefix",
            "input_mem_file": "input.mem",
            "output_dir": "/tmp",
        }

        # Test cases with invalid values
        invalid_test_cases = [
            # Test negative hbm_size
            {**base_kwargs, "hbm_size": -1024},
            # Test non-integer hbm_size
            {**base_kwargs, "hbm_size": "not_an_integer"},
            # Test invalid boolean value for has_hbm
            {**base_kwargs, "has_hbm": "not_a_boolean"},
        ]

        # Act & Assert
        for test_case in invalid_test_cases:
            with patch("assembler.common.makeUniquePath", side_effect=lambda x: x):
                with pytest.raises(ValueError, match=r".*invalid.*|.*Invalid.*"):
                    LinkerRunConfig(**test_case)
