# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the program_linker_utils module.
"""

from unittest.mock import MagicMock, patch

import pytest
from linker.instructions import cinst, minst
from linker.kern_trace.kernel_info import InstrAct
from linker.steps.program_linker_utils import (
    calculate_instruction_latency_adjustment,
    process_bload_instructions,
    remove_csyncm,
    search_minstrs_back,
    search_minstrs_forward,
)


class TestCalculateInstructionLatencyAdjustment:
    """@brief Tests for calculate_instruction_latency_adjustment function."""

    @patch("assembler.instructions.cinst.CLoad.get_latency", return_value=5)
    def test_cload_latency(self, mock_get_latency):
        """@brief Test latency calculation for CLoad instruction."""
        mock_cload = MagicMock(spec=cinst.CLoad)

        result = calculate_instruction_latency_adjustment(mock_cload)

        assert result == 5
        mock_get_latency.assert_called_once()

    @patch("assembler.instructions.cinst.BLoad.get_latency", return_value=3)
    def test_bload_latency(self, mock_get_latency):
        """@brief Test latency calculation for BLoad instruction."""
        mock_bload = MagicMock(spec=cinst.BLoad)

        result = calculate_instruction_latency_adjustment(mock_bload)

        assert result == 3
        mock_get_latency.assert_called_once()

    @patch("assembler.instructions.cinst.BOnes.get_latency", return_value=2)
    def test_bones_latency(self, mock_get_latency):
        """@brief Test latency calculation for BOnes instruction."""
        mock_bones = MagicMock(spec=cinst.BOnes)

        result = calculate_instruction_latency_adjustment(mock_bones)

        assert result == 2
        mock_get_latency.assert_called_once()

    def test_unknown_instruction_latency(self):
        """@brief Test latency calculation for unknown instruction type."""
        mock_unknown = MagicMock()

        result = calculate_instruction_latency_adjustment(mock_unknown)

        assert result == 0

    def test_none_instruction(self):
        """@brief Test latency calculation for None instruction."""
        result = calculate_instruction_latency_adjustment(None)

        assert result == 0


class TestProcessBloadInstructions:
    """@brief Tests for process_bload_instructions function."""

    def test_process_single_bload_not_in_tracker(self):
        """@brief Test processing single BLoad not in tracker."""
        mock_bload = MagicMock(spec=cinst.BLoad)
        mock_bload.var_name = "var1"

        kernel_cinstrs = [mock_bload]

        mock_map_entry = MagicMock()
        kernel_cinstrs_map = [mock_map_entry]

        cinst_in_var_tracker = {}

        result = process_bload_instructions(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, 0)

        assert result == 0  # idx - 1
        # Action should not be modified since var not in tracker
        assert mock_map_entry.action != InstrAct.SKIP

    def test_process_single_bload_in_tracker(self):
        """@brief Test processing single BLoad in tracker."""
        mock_bload = MagicMock(spec=cinst.BLoad)
        mock_bload.var_name = "var1"

        kernel_cinstrs = [mock_bload]

        mock_map_entry = MagicMock()
        kernel_cinstrs_map = [mock_map_entry]

        cinst_in_var_tracker = {"var1": 0}

        result = process_bload_instructions(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, 0)

        assert result == 0  # idx - 1
        assert mock_map_entry.action == InstrAct.SKIP

    def test_process_multiple_bload_instructions(self):
        """@brief Test processing multiple consecutive BLoad instructions."""
        mock_bload1 = MagicMock(spec=cinst.BLoad)
        mock_bload1.var_name = "var1"

        mock_bload2 = MagicMock(spec=cinst.BLoad)
        mock_bload2.var_name = "var2"

        mock_bload3 = MagicMock(spec=cinst.BLoad)
        mock_bload3.var_name = "var3"

        kernel_cinstrs = [mock_bload1, mock_bload2, mock_bload3]

        mock_map_entries = [MagicMock(), MagicMock(), MagicMock()]
        kernel_cinstrs_map = mock_map_entries

        cinst_in_var_tracker = {"var2": 1}  # Only var2 is tracked

        result = process_bload_instructions(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, 0)

        assert result == 2  # 3 - 1
        # Only var2 should be marked as SKIP
        assert mock_map_entries[1].action == InstrAct.SKIP
        assert mock_map_entries[0].action != InstrAct.SKIP
        assert mock_map_entries[2].action != InstrAct.SKIP

    def test_process_bload_mixed_with_other_instructions(self):
        """@brief Test processing BLoad when followed by non-BLoad instruction."""
        mock_bload = MagicMock(spec=cinst.BLoad)
        mock_bload.var_name = "var1"

        mock_cload = MagicMock(spec=cinst.CLoad)

        kernel_cinstrs = [mock_bload, mock_cload]

        mock_map_entries = [MagicMock(), MagicMock()]
        kernel_cinstrs_map = mock_map_entries

        cinst_in_var_tracker = {}

        result = process_bload_instructions(kernel_cinstrs, kernel_cinstrs_map, cinst_in_var_tracker, 0)

        assert result == 0  # Stopped at first non-BLoad, so 1 - 1 = 0


class TestRemoveCsyncm:
    """@brief Tests for remove_csyncm function."""

    @patch("assembler.instructions.cinst.CSyncm.get_throughput", return_value=4)
    def test_remove_valid_csyncm(self, mock_get_throughput):
        """@brief Test removing valid CSyncm instruction."""
        mock_csyncm = MagicMock(spec=cinst.CSyncm)

        kernel_cinstrs = [mock_csyncm]

        mock_map_entry = MagicMock()
        kernel_cinstrs_map = [mock_map_entry]

        adjust_idx, adjust_cycles = remove_csyncm(kernel_cinstrs, kernel_cinstrs_map, 0)

        assert adjust_idx == -1
        assert adjust_cycles == 4
        assert mock_map_entry.action == InstrAct.SKIP
        mock_get_throughput.assert_called_once()

    def test_remove_non_csyncm_instruction(self):
        """@brief Test attempting to remove non-CSyncm instruction."""
        mock_cload = MagicMock(spec=cinst.CLoad)

        kernel_cinstrs = [mock_cload]

        mock_map_entry = MagicMock()
        kernel_cinstrs_map = [mock_map_entry]

        adjust_idx, adjust_cycles = remove_csyncm(kernel_cinstrs, kernel_cinstrs_map, 0)

        assert adjust_idx == 0
        assert adjust_cycles == 0
        assert mock_map_entry.action != InstrAct.SKIP

    def test_remove_csyncm_invalid_index_negative(self):
        """@brief Test removing CSyncm with negative index."""
        kernel_cinstrs = []
        kernel_cinstrs_map = []

        adjust_idx, adjust_cycles = remove_csyncm(kernel_cinstrs, kernel_cinstrs_map, -1)

        assert adjust_idx == 0
        assert adjust_cycles == 0

    def test_remove_csyncm_invalid_index_too_large(self):
        """@brief Test removing CSyncm with index larger than list."""
        mock_cload = MagicMock(spec=cinst.CLoad)

        kernel_cinstrs = [mock_cload]
        kernel_cinstrs_map = [MagicMock()]

        adjust_idx, adjust_cycles = remove_csyncm(kernel_cinstrs, kernel_cinstrs_map, 5)

        assert adjust_idx == 0
        assert adjust_cycles == 0

    def test_remove_csyncm_empty_lists(self):
        """@brief Test removing CSyncm from empty lists."""
        adjust_idx, adjust_cycles = remove_csyncm([], [], 0)

        assert adjust_idx == 0
        assert adjust_cycles == 0


class TestSearchMinstrsBack:
    """@brief Tests for search_minstrs_back function."""

    def test_search_minstrs_back_found(self):
        """@brief Test searching backwards and finding MLoad."""
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_msyncc = MagicMock(spec=minst.MSyncc)

        mock_entry1 = MagicMock()
        mock_entry1.minstr = mock_msyncc
        mock_entry1.spad_addr = -1

        mock_entry2 = MagicMock()
        mock_entry2.minstr = mock_mload
        mock_entry2.spad_addr = 10

        minstrs_map = [mock_entry1, mock_entry2]

        result = search_minstrs_back(minstrs_map, 1, 10)

        assert result == 1

    def test_search_minstrs_back_found_earlier_index(self):
        """@brief Test searching backwards and finding MLoad at earlier index."""
        mock_mload1 = MagicMock(spec=minst.MLoad)
        mock_mload2 = MagicMock(spec=minst.MLoad)
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry1 = MagicMock()
        mock_entry1.minstr = mock_mload1
        mock_entry1.spad_addr = 5

        mock_entry2 = MagicMock()
        mock_entry2.minstr = mock_mload2
        mock_entry2.spad_addr = 10

        mock_entry3 = MagicMock()
        mock_entry3.minstr = mock_mstore
        mock_entry3.spad_addr = 15

        minstrs_map = [mock_entry1, mock_entry2, mock_entry3]

        result = search_minstrs_back(minstrs_map, 2, 5)

        assert result == 0

    def test_search_minstrs_back_not_found(self):
        """@brief Test searching backwards when MLoad not found."""
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_mstore
        mock_entry.spad_addr = 10

        minstrs_map = [mock_entry]

        with pytest.raises(RuntimeError, match="Could not find MLoad with SPAD address 20"):
            search_minstrs_back(minstrs_map, 0, 20)

    def test_search_minstrs_back_wrong_spad_address(self):
        """@brief Test searching backwards with wrong SPAD address."""
        mock_mload = MagicMock(spec=minst.MLoad)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_mload
        mock_entry.spad_addr = 5

        minstrs_map = [mock_entry]

        with pytest.raises(RuntimeError, match="Could not find MLoad with SPAD address 10"):
            search_minstrs_back(minstrs_map, 0, 10)

    def test_search_minstrs_back_empty_map(self):
        """@brief Test searching backwards in empty map."""
        with pytest.raises(IndexError, match="Index 0 is out of bounds for minstrs_map"):
            search_minstrs_back([], 0, 10)


class TestSearchMinstrsForward:
    """@brief Tests for search_minstrs_forward function."""

    def test_search_minstrs_forward_found_mstore(self):
        """@brief Test searching forward and finding MStore."""
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry1 = MagicMock()
        mock_entry1.minstr = mock_mload
        mock_entry1.spad_addr = 5

        mock_entry2 = MagicMock()
        mock_entry2.minstr = mock_mstore
        mock_entry2.spad_addr = 10

        minstrs_map = [mock_entry1, mock_entry2]

        result = search_minstrs_forward(minstrs_map, 0, 10)

        assert result == 1

    def test_search_minstrs_forward_found_mload(self):
        """@brief Test searching forward and finding MLoad."""
        mock_mload1 = MagicMock(spec=minst.MLoad)
        mock_mload2 = MagicMock(spec=minst.MLoad)

        mock_entry1 = MagicMock()
        mock_entry1.minstr = mock_mload1
        mock_entry1.spad_addr = 5

        mock_entry2 = MagicMock()
        mock_entry2.minstr = mock_mload2
        mock_entry2.spad_addr = 10

        minstrs_map = [mock_entry1, mock_entry2]

        result = search_minstrs_forward(minstrs_map, 0, 10)

        assert result == 1

    def test_search_minstrs_forward_found_at_start_index(self):
        """@brief Test searching forward and finding at start index."""
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_mstore
        mock_entry.spad_addr = 10

        minstrs_map = [mock_entry]

        result = search_minstrs_forward(minstrs_map, 0, 10)

        assert result == 0

    def test_search_minstrs_forward_not_found(self):
        """@brief Test searching forward when instruction not found."""
        mock_msyncc = MagicMock(spec=minst.MSyncc)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_msyncc
        mock_entry.spad_addr = -1

        minstrs_map = [mock_entry]

        with pytest.raises(RuntimeError, match="Could not find MStore with SPAD address 10"):
            search_minstrs_forward(minstrs_map, 0, 10)

    def test_search_minstrs_forward_wrong_spad_address(self):
        """@brief Test searching forward with wrong SPAD address."""
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_mstore
        mock_entry.spad_addr = 5

        minstrs_map = [mock_entry]

        with pytest.raises(RuntimeError, match="Could not find MStore with SPAD address 10"):
            search_minstrs_forward(minstrs_map, 0, 10)

    def test_search_minstrs_forward_start_beyond_range(self):
        """@brief Test searching forward starting beyond map range."""
        mock_mstore = MagicMock(spec=minst.MStore)

        mock_entry = MagicMock()
        mock_entry.minstr = mock_mstore
        mock_entry.spad_addr = 10

        minstrs_map = [mock_entry]

        with pytest.raises(RuntimeError, match="Could not find MStore with SPAD address 10"):
            search_minstrs_forward(minstrs_map, 5, 10)

    def test_search_minstrs_forward_empty_map(self):
        """@brief Test searching forward in empty map."""
        with pytest.raises(RuntimeError, match="Could not find MStore with SPAD address 10"):
            search_minstrs_forward([], 0, 10)
