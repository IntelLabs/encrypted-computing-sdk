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

# Add the parent directory to sys.path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(autouse=True)
def mock_env_variables():
    """
    @brief Fixture to mock environment variables and provide common mocks
    """
    with patch.dict(
        "os.environ",
        {"PYTHONPATH": "/home/jmrojasc/test/linker_sdk/encrypted-computing-sdk"},
    ):
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
            This fixture is intended to be run from the assembler root directory.

    Yields:
            None

    Raises:
            Any exceptions raised by ISASpecConfig.initialize_isa_spec or
            MemSpecConfig.initialize_mem_spec will propagate.
    """
    module_dir = os.path.dirname(os.path.dirname(__file__))
    ISASpecConfig.initialize_isa_spec(module_dir, "")
    MemSpecConfig.initialize_mem_spec(module_dir, "")
