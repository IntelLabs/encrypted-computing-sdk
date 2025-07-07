# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@file conftest.py
@brief Configuration and fixtures for pytest
"""

import os
import sys
from unittest.mock import patch

import pytest

from assembler.spec_config.isa_spec import ISASpecConfig
from assembler.spec_config.mem_spec import MemSpecConfig

# Remove any existing paths that might conflict
for path in list(sys.path):
    if "hec-assembler-tools" in path:
        sys.path.remove(path)

# Get the absolute path to the repository root directory
# Structure: /path/to/repo/encrypted-computing-sdk/assembler_tools/linker_sdk/tests/conftest.py
current_dir = os.path.dirname(os.path.abspath(__file__))
linker_sdk_dir = os.path.dirname(current_dir)  # linker_sdk directory
assembler_tools_dir = os.path.dirname(linker_sdk_dir)  # assembler_tools directory
repo_root = os.path.dirname(assembler_tools_dir)  # encrypted-computing-sdk directory

# Add the paths to sys.path
sys.path.insert(0, linker_sdk_dir)
sys.path.insert(0, assembler_tools_dir)
sys.path.insert(0, repo_root)


@pytest.fixture(autouse=True)
def mock_env_variables():
    """
    @brief Fixture to mock environment variables and provide common mocks
    """
    # Use the repository root in PYTHONPATH instead of an absolute path
    with patch.dict("os.environ", {"PYTHONPATH": repo_root}):
        yield


@pytest.fixture(scope="session", autouse=True)
def initialize_specs():
    """
    Fixture to initialize ISA and memory specifications for test session.

    This fixture is automatically used for the entire test session and ensures that
    the ISA and memory specifications are initialized before any tests are run.
    It determines the module directory relative to the current file and calls the
    initialization methods for both ISASpecConfig and MemSpecConfig.

    Note:
            This fixture is intended to be run from any location.

    Yields:
            None

    Raises:
            Any exceptions raised by ISASpecConfig.initialize_isa_spec or
            MemSpecConfig.initialize_mem_spec will propagate.
    """
    module_dir = linker_sdk_dir
    ISASpecConfig.initialize_isa_spec(module_dir, "")
    MemSpecConfig.initialize_mem_spec(module_dir, "")
