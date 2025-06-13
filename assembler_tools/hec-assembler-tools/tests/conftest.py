# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Pytest configuration and fixtures for assembler_tools tests.
"""

import os
import pytest
from assembler.spec_config.isa_spec import ISASpecConfig
from assembler.spec_config.mem_spec import MemSpecConfig


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
