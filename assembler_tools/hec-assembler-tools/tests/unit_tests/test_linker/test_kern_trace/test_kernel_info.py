# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_kernel_info.py
@brief Unit tests for the KernelInfo class
"""

from linker.kern_trace.kernel_info import KernelInfo


class TestKernelInfo:
    """
    @class TestKernelInfo
    @brief Test cases for the KernelInfo class
    """

    def test_kernel_files_creation(self):
        """
        @brief Test KernelInfo creation and attribute access
        """
        # Act
        kernel_files = KernelInfo(
            {
                "directory": "/tmp/dir",
                "prefix": "prefix",
                "minst": "prefix.minst",
                "cinst": "prefix.cinst",
                "xinst": "prefix.xinst",
                "mem": "prefix.mem",
            }
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
        @brief Test KernelInfo creation without mem file
        """
        # Act
        kernel_files = KernelInfo(
            {
                "directory": "/tmp/dir",
                "prefix": "prefix",
                "minst": "prefix.minst",
                "cinst": "prefix.cinst",
                "xinst": "prefix.xinst",
            }
        )

        # Assert
        assert kernel_files.directory == "/tmp/dir"
        assert kernel_files.prefix == "prefix"
        assert kernel_files.minst == "prefix.minst"
        assert kernel_files.cinst == "prefix.cinst"
        assert kernel_files.xinst == "prefix.xinst"
        assert kernel_files.mem is None
