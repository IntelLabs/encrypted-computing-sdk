# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_kernel_info.py
@brief Unit tests for the KernelInfo class
"""

from unittest.mock import MagicMock

import pytest
from linker.instructions import cinst, minst
from linker.kern_trace.kernel_info import InstrAct, KernelInfo


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

    def test_files_property(self):
        """
        @brief Test files property returns correct list of files
        """
        # With mem file
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

        expected_files = ["prefix.minst", "prefix.cinst", "prefix.xinst", "prefix.mem"]
        assert kernel_files.files == expected_files

        # Without mem file
        kernel_files_no_mem = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        expected_files_no_mem = ["prefix.minst", "prefix.cinst", "prefix.xinst"]
        assert kernel_files_no_mem.files == expected_files_no_mem

    def test_hbm_remap_dict_property(self):
        """
        @brief Test hbm_remap_dict getter and setter
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test initial empty dict
        assert kernel_files.hbm_remap_dict == {}

        # Test setter with valid dict
        remap_dict = {"old_var": "new_var", "var1": "var2"}
        kernel_files.hbm_remap_dict = remap_dict
        assert kernel_files.hbm_remap_dict == remap_dict

        # Test setter with invalid type
        with pytest.raises(TypeError, match="Remap dictionary must be of type dict"):
            kernel_files.hbm_remap_dict = ["not", "a", "dict"]

    def test_spad_size_property(self):
        """
        @brief Test spad_size getter and setter
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test initial value
        assert kernel_files.spad_size == 0

        # Test setter with valid int
        kernel_files.spad_size = 42
        assert kernel_files.spad_size == 42

        # Test setter with invalid type
        with pytest.raises(TypeError, match="Scratchpad offset must be an integer"):
            kernel_files.spad_size = "not an int"

    def test_minstrs_property_and_map_filling(self):
        """
        @brief Test minstrs property and automatic map filling
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Create mock instructions
        mock_mload = MagicMock()
        mock_mload.spad_address = 10

        mock_msyncc = MagicMock(spec=minst.MSyncc)

        mock_mstore = MagicMock()
        mock_mstore.spad_address = 20

        minstrs = [mock_mload, mock_msyncc, mock_mstore]

        # Test setter
        kernel_files.minstrs = minstrs
        assert kernel_files.minstrs == minstrs

        # Test that minstrs_map was automatically filled
        assert len(kernel_files.minstrs_map) == 3

        # Check first entry (mload)
        assert kernel_files.minstrs_map[0].spad_addr == 10
        assert kernel_files.minstrs_map[0].minstr == mock_mload
        assert kernel_files.minstrs_map[0].action == InstrAct.KEEP_HBM

        # Check second entry (msyncc - should have spad_addr -1)
        assert kernel_files.minstrs_map[1].spad_addr == -1
        assert kernel_files.minstrs_map[1].minstr == mock_msyncc
        assert kernel_files.minstrs_map[1].action == InstrAct.KEEP_HBM

        # Check third entry (mstore)
        assert kernel_files.minstrs_map[2].spad_addr == 20
        assert kernel_files.minstrs_map[2].minstr == mock_mstore
        assert kernel_files.minstrs_map[2].action == InstrAct.KEEP_HBM

    def test_minstrs_map_property(self):
        """
        @brief Test minstrs_map getter and setter
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test initial empty list
        assert kernel_files.minstrs_map == []

        # Test setter with valid list
        mock_entry = MagicMock()
        new_map = [mock_entry]
        kernel_files.minstrs_map = new_map
        assert kernel_files.minstrs_map == new_map

        # Test setter with invalid type
        with pytest.raises(TypeError, match="minstrs_map must be a list"):
            kernel_files.minstrs_map = "not a list"

    def test_cinstrs_property_and_map_filling(self):
        """
        @brief Test cinstrs property and automatic map filling
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Create mock instructions
        mock_cload = MagicMock(spec=cinst.CLoad)
        mock_cload.tokens = ["0", "cload", "reg1", "var1"]

        mock_csyncm = MagicMock()
        mock_csyncm.tokens = ["1", "csyncm", "5"]

        mock_bload = MagicMock(spec=cinst.BLoad)
        mock_bload.tokens = ["2", "bload", "reg2", "var2"]

        cinstrs = [mock_cload, mock_csyncm, mock_bload]

        # Test setter
        kernel_files.cinstrs = cinstrs
        assert kernel_files.cinstrs == cinstrs

        # Test that cinstrs_map was automatically filled
        assert len(kernel_files.cinstrs_map) == 3

        # Check first entry (cload - should have reg_name from tokens[2])
        assert kernel_files.cinstrs_map[0].reg_name == "reg1"
        assert kernel_files.cinstrs_map[0].cinstr == mock_cload
        assert kernel_files.cinstrs_map[0].action == InstrAct.KEEP_SPAD

        # Check second entry (csyncm - should have empty reg_name)
        assert kernel_files.cinstrs_map[1].reg_name == ""
        assert kernel_files.cinstrs_map[1].cinstr == mock_csyncm
        assert kernel_files.cinstrs_map[1].action == InstrAct.KEEP_SPAD

        # Check third entry (bload - should have reg_name from tokens[2])
        assert kernel_files.cinstrs_map[2].reg_name == "reg2"
        assert kernel_files.cinstrs_map[2].cinstr == mock_bload
        assert kernel_files.cinstrs_map[2].action == InstrAct.KEEP_SPAD

    def test_cinstrs_map_property(self):
        """
        @brief Test cinstrs_map getter and setter
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test initial empty list
        assert kernel_files.cinstrs_map == []

        # Test setter with valid list
        mock_entry = MagicMock()
        new_map = [mock_entry]
        kernel_files.cinstrs_map = new_map
        assert kernel_files.cinstrs_map == new_map

        # Test setter with invalid type
        with pytest.raises(TypeError, match="cinstrs_map must be a list"):
            kernel_files.cinstrs_map = "not a list"

    def test_xinstrs_property(self):
        """
        @brief Test xinstrs property getter and setter
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test initial empty list
        assert kernel_files.xinstrs == []

        # Test setter with valid list
        mock_xinstr = MagicMock()
        xinstrs = [mock_xinstr]
        kernel_files.xinstrs = xinstrs
        assert kernel_files.xinstrs == xinstrs

        # Test setter with invalid type
        with pytest.raises(TypeError, match="xinstrs must be a list"):
            kernel_files.xinstrs = None

    def test_cinstrs_setter_with_none(self):
        """
        @brief Test cinstrs setter with None value
        """
        kernel_files = KernelInfo(
            {"directory": "/tmp/dir", "prefix": "prefix", "minst": "prefix.minst", "cinst": "prefix.cinst", "xinst": "prefix.xinst"}
        )

        # Test setter with invalid type
        with pytest.raises(TypeError, match="cinstrs must be a list"):
            kernel_files.cinstrs = None
