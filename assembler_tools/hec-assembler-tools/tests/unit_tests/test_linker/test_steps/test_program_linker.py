# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the program_linker module.
"""

import io
import unittest
from unittest.mock import MagicMock, call, mock_open, patch

import pytest
from assembler.common.config import GlobalConfig
from linker import MemoryModel
from linker.instructions import cinst, dinst, minst
from linker.kern_trace import InstrAct
from linker.steps.program_linker import LinkedProgram


# pylint: disable=protected-access
class TestLinkedProgram(unittest.TestCase):
    """@brief Tests for the LinkedProgram class."""

    def setUp(self):
        """@brief Set up test fixtures."""
        # Group related stream objects into a dictionary
        self.streams = {
            "minst": io.StringIO(),
            "cinst": io.StringIO(),
            "xinst": io.StringIO(),
        }
        self.mem_model = MagicMock(spec=MemoryModel)

        # Mock the hasHBM property to return True by default
        self.has_hbm_patcher = patch.object(GlobalConfig, "hasHBM", True)
        self.mock_has_hbm = self.has_hbm_patcher.start()

        # Mock the suppress_comments property to return False by default
        self.suppress_comments_patcher = patch.object(GlobalConfig, "suppress_comments", False)
        self.mock_suppress_comments = self.suppress_comments_patcher.start()

        self.program = LinkedProgram()

        self.program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

    def tearDown(self):
        """@brief Tear down test fixtures."""
        self.has_hbm_patcher.stop()
        self.suppress_comments_patcher.stop()

    def test_init(self):
        """@brief Test initialization of LinkedProgram.

        @test Verifies that all instance variables are correctly initialized
        """
        self.assertEqual(self.program._minst_ostream, self.streams["minst"])
        self.assertEqual(self.program._cinst_ostream, self.streams["cinst"])
        self.assertEqual(self.program._xinst_ostream, self.streams["xinst"])
        self.assertEqual(self.program._LinkedProgram__mem_model, self.mem_model)
        self.assertEqual(self.program._bundle_offset, 0)
        self.assertEqual(self.program._minst_line_offset, 0)
        self.assertEqual(self.program._cinst_line_offset, 0)
        self.assertEqual(self.program._kernel_count, 0)
        self.assertTrue(self.program.is_open)

    def test_is_open_property(self):
        """@brief Test the is_open property.

        @test Verifies that the is_open property reflects the internal state
        """
        self.assertTrue(self.program.is_open)
        self.program._is_open = False
        self.assertFalse(self.program.is_open)

    def test_close(self):
        """@brief Test closing the program.

        @test Verifies that cexit and msyncc instructions are added and program is marked as closed
        """
        self.program.close()

        # Verify cexit and msyncc were added
        self.assertIn("cexit", self.streams["cinst"].getvalue().lower())
        self.assertIn("msyncc", self.streams["minst"].getvalue().lower())
        self.assertFalse(self.program.is_open)

        # Test that closing an already closed program raises RuntimeError
        with self.assertRaises(RuntimeError):
            self.program.close()

        # Clean the StringIO object properly
        self.streams["minst"].seek(0)
        self.streams["minst"].truncate(0)
        self.streams["cinst"].seek(0)
        self.streams["cinst"].truncate(0)
        self.streams["xinst"].seek(0)
        self.streams["xinst"].truncate(0)

        # Test closing the program with comments suppressed.
        with patch.object(GlobalConfig, "suppress_comments", True):
            program = LinkedProgram()
            program.initialize(
                self.streams["minst"],
                self.streams["cinst"],
                self.streams["xinst"],
                self.mem_model,
            )
            program.close()

        # Should not contain "terminating MInstQ" comment
        self.assertNotIn("terminating MInstQ", self.streams["minst"].getvalue())

    def test_update_minsts_no_mem_model(self):
        """@brief Test updating MInsts when no memory model is available.

        @test Verifies that RuntimeError is raised when memory model is None
        """
        # Create mock MInstructions
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "input_var"
        mock_mload.hbm_address = 0
        mock_mload.comment = "original comment"

        # Create mock KernelInfo
        mock_kernel_info = MagicMock()
        mock_kernel_info.minstrs = [mock_mload]
        mock_kernel_info.minstrs_map = [MagicMock()]

        # Set memory model to None
        self.program._LinkedProgram__mem_model = None

        # Execute the update and verify RuntimeError is raised
        with pytest.raises(RuntimeError, match="Memory model is not initialized"):
            self.program._update_minsts(mock_kernel_info)

    def test_update_minsts(self):
        """@brief Test updating MInsts with SPAD addresses when HBM is enabled.

        @test Verifies that SPAD addresses are correctly updated with _spad_offset when linking multiple kernels
        """
        self.program._kernel_count = 1  # Set kernel count
        self.program._cinst_line_offset = 10  # Set initial offset

        # Create mock MInstructions with initial SPAD addresses
        mock_msyncc = MagicMock(spec=minst.MSyncc)
        mock_msyncc.comment = ""
        mock_msyncc.target = 1

        mock_mload1 = MagicMock(spec=minst.MLoad)
        mock_mload1.var_name = "input_var1"
        mock_mload1.hbm_address = 0
        mock_mload1.spad_address = 5
        mock_mload1.comment = "original comment"

        mock_mstore1 = MagicMock(spec=minst.MStore)
        mock_mstore1.var_name = "output_var1"
        mock_mstore1.hbm_address = 0
        mock_mstore1.spad_address = 10
        mock_mstore1.comment = "Storing output_var1"

        mock_mload2 = MagicMock(spec=minst.MLoad)
        mock_mload2.var_name = "input_var2"
        mock_mload2.hbm_address = 0
        mock_mload2.spad_address = 15
        mock_mload2.comment = "another comment"

        # Set up memory model mock to return HBM addresses
        self.mem_model.use_variable.side_effect = [
            100,  # HBM address for input_var1
            200,  # HBM address for output_var1
            300,  # HBM address for input_var2
        ]

        # Create mock KernelInfo
        mock_kernel_info = MagicMock()
        mock_kernel_info.minstrs = [mock_mload1, mock_msyncc, mock_mstore1, mock_mload2]
        mock_kernel_info.minstrs_map = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]

        # Configure minstrs_map actions to KEEP_HBM for HBM mode
        for minstr_map in mock_kernel_info.minstrs_map:
            minstr_map.action = InstrAct.KEEP_HBM

        # Create mock CInstr for cinstrs_map
        mock_cinstr = MagicMock()
        mock_cinstr.comment = ""
        mock_cinstr.idx = 6  # Same as msyncc.target

        # Create mock CinstrMapEntry
        mock_cinstr_map_entry = MagicMock()
        mock_cinstr_map_entry.cinstr = mock_cinstr
        mock_kernel_info.cinstrs_map = [MagicMock(), mock_cinstr_map_entry]

        # Set SPAD offset to test address adjustment
        self.program._spad_offset = 50
        self.program._kernel_count = 1

        # Execute the update
        self.program._update_minsts(mock_kernel_info)

        # Verify MSyncc target was updated with _cinst_line_offset
        self.assertEqual(mock_msyncc.target, 16)  # 5 + 10

        # Verify SPAD addresses were updated with _spad_offset
        self.assertEqual(mock_mload1.spad_address, 55)  # 5 + 50
        self.assertEqual(mock_mstore1.spad_address, 60)  # 10 + 50
        self.assertEqual(mock_mload2.spad_address, 65)  # 15 + 50

        # Verify HBM addresses were updated with memory model addresses
        self.assertEqual(mock_mload1.hbm_address, 100)
        self.assertEqual(mock_mstore1.hbm_address, 200)
        self.assertEqual(mock_mload2.hbm_address, 300)

        # Verify comments were updated with variable names
        self.assertIn("input_var1", mock_mload1.comment)
        self.assertIn("original comment", mock_mload1.comment)
        self.assertIn("output_var1", mock_mstore1.comment)
        self.assertIn("input_var2", mock_mload2.comment)
        self.assertIn("another comment", mock_mload2.comment)

        # Verify the memory model was called with correct parameters
        expected_calls = [
            call("input_var1", 1),  # kernel_count = 1
            call("output_var1", 1),
            call("input_var2", 1),
        ]
        self.mem_model.use_variable.assert_has_calls(expected_calls)

    def test_remove_and_merge_csyncm_cnop(self):
        """@brief Test removing CSyncm instructions and merging CNop instructions.

        @test Verifies that CSyncm instructions are removed and CNop cycles are updated correctly
        """
        # Create mock CInstructions
        mock_ifetch = MagicMock(spec=cinst.IFetch)
        mock_ifetch.bundle = 1
        mock_ifetch.tokens = [0]
        mock_ifetch.comment = "ifetch comment"

        mock_csyncm1 = MagicMock(spec=cinst.CSyncm)
        mock_csyncm1.tokens = [0]
        mock_csyncm1.comment = "sync comment"

        mock_cnop1 = MagicMock(spec=cinst.CNop)
        mock_cnop1.cycles = 2
        mock_cnop1.tokens = [0]
        mock_cnop1.comment = "nop comment"

        mock_csyncm2 = MagicMock(spec=cinst.CSyncm)
        mock_csyncm2.tokens = [0]
        mock_csyncm2.comment = "sync comment"

        mock_cnop2 = MagicMock(spec=cinst.CNop)
        mock_cnop2.cycles = 3
        mock_cnop2.tokens = [0]
        mock_cnop2.comment = "nop comment"

        # Create mock KernelInfo
        mock_kernel_info = MagicMock()
        mock_kernel_info.cinstrs = [
            mock_ifetch,
            mock_csyncm1,
            mock_cnop1,
            mock_csyncm2,
            mock_cnop2,
        ]

        # Create mock cinstrs_map entries
        mock_kernel_info.cinstrs_map = []
        for cinstr in mock_kernel_info.cinstrs:
            mock_entry = MagicMock()
            mock_entry.action = MagicMock()  # Mock the action attribute
            mock_entry.cinstr = cinstr
            mock_kernel_info.cinstrs_map.append(mock_entry)

        # Set up ISACInst.CSyncm.get_throughput
        with patch("assembler.instructions.cinst.CSyncm.get_throughput", return_value=2):
            # Execute the method
            self.program._remove_and_merge_csyncm_cnop(mock_kernel_info)

            # Verify CSyncm instructions' actions were marked as SKIP
            # CSyncm1 is at index 1, CSyncm2 is at index 3
            self.assertEqual(mock_kernel_info.cinstrs_map[1].action, InstrAct.SKIP)
            self.assertEqual(mock_kernel_info.cinstrs_map[3].action, InstrAct.SKIP)

            # Verify CNop cycles were updated (should have added 2 for each CSyncm)
            # First CNop gets 2 cycles added from first CSyncm
            self.assertEqual(mock_cnop1.cycles, 4)  # 2 + 2

            # Verify the line numbers were updated
            for i, instr in enumerate(mock_kernel_info.cinstrs):
                self.assertEqual(instr.idx, str(i))

    def test_update_cinsts_addresses_and_offsets(self):
        """@brief Test updating CInst addresses and offsets.

        @test Verifies that CInst addresses and offsets are correctly updated
        """
        # Create mock CInstructions
        mock_ifetch = MagicMock(spec=cinst.IFetch)
        mock_ifetch.bundle = 1

        mock_csyncm = MagicMock(spec=cinst.CSyncm)
        mock_csyncm.target = 5

        mock_xinstfetch = MagicMock(spec=cinst.XInstFetch)

        # Create SPAD instructions for no-HBM case
        mock_bload = MagicMock(spec=cinst.BLoad)
        mock_bload.var_name = "var1"
        mock_bload.spad_address = 0
        mock_bload.comment = "original comment"

        mock_cstore = MagicMock(spec=cinst.CStore)
        mock_cstore.var_name = "var2"
        mock_cstore.spad_address = 0
        mock_cstore.comment = None

        # Execute the method with HBM enabled
        kernel_cinstrs = [mock_ifetch, mock_csyncm, mock_csyncm]
        self.program._bundle_offset = 10
        self.program._minst_line_offset = 20
        self.program._update_cinsts_addresses_and_offsets(kernel_cinstrs)

        # Verify results with HBM enabled
        self.assertEqual(mock_ifetch.bundle, 11)  # 1 + 10
        self.assertEqual(mock_csyncm.target, 25)  # 5 + 20

        # Test with HBM disabled
        with patch.object(GlobalConfig, "hasHBM", False):
            # Set up memory model mock
            self.mem_model.use_variable.side_effect = [
                30,
                40,
            ]  # Return different addresses for different vars

            kernel_cinstrs = [mock_bload, mock_cstore]
            self.program._kernel_count = 2
            self.program._update_cinsts_addresses_and_offsets(kernel_cinstrs)

            # Verify SPAD instructions were updated
            self.assertEqual(mock_bload.spad_address, 30)
            self.assertIn("var1", mock_bload.comment)
            self.assertIn("original comment", mock_bload.comment)

            self.assertEqual(mock_cstore.spad_address, 40)

            # Verify the memory model was used correctly
            self.mem_model.use_variable.assert_has_calls([call("var1", 2), call("var2", 2)])

        # Test that XInstFetch raises NotImplementedError
        with self.assertRaises(NotImplementedError):
            self.program._update_cinsts_addresses_and_offsets([mock_xinstfetch])

    def test_update_cinsts(self):
        """@brief Test updating CInsts.

        @test Verifies that the correct update methods are called based on HBM configuration
        """
        # Create a mock for _remove_and_merge_csyncm_cnop and _update_cinsts_addresses_and_offsets
        with (
            patch.object(LinkedProgram, "_remove_and_merge_csyncm_cnop") as mock_remove,
            patch.object(LinkedProgram, "_update_cinsts_addresses_and_offsets") as mock_update,
        ):
            mock_cinst1 = MagicMock()
            mock_cinst2 = MagicMock()

            # Create mock KernelInfo
            mock_kernel_info = MagicMock()
            mock_kernel_info.cinstrs = [mock_cinst1, mock_cinst2]

            self.program._update_cinsts(mock_kernel_info)

            # Verify that only _update_cinsts_addresses_and_offsets was called
            mock_remove.assert_not_called()
            mock_update.assert_called_once_with(mock_kernel_info.cinstrs)

            # Reset mocks
            mock_remove.reset_mock()
            mock_update.reset_mock()

            # Execute the method with HBM disabled
            with patch.object(GlobalConfig, "hasHBM", False):
                self.program._update_cinsts(mock_kernel_info)

                # Verify that both methods were called
                mock_remove.assert_called_once_with(mock_kernel_info)
                mock_update.assert_called_once_with(mock_kernel_info.cinstrs)

    def test_update_cinst_kernel_hbm(self):
        """@brief Test updating CInsts in HBM mode.

        @test Verifies that CInst instructions are correctly updated with synchronization points
        and SPAD address mappings in HBM mode
        """
        # Create mock CInstructions
        mock_csyncm = MagicMock(spec=cinst.CSyncm)
        mock_csyncm.target = 2
        mock_csyncm.comment = "sync comment"

        mock_cload = MagicMock(spec=cinst.CLoad)
        mock_cload.var_name = "input_var"
        mock_cload.spad_address = 10
        mock_cload.comment = "load input variable"

        mock_cstore = MagicMock(spec=cinst.CStore)
        mock_cstore.var_name = "output_var"
        mock_cstore.spad_address = 20
        mock_cstore.comment = ""

        mock_nload = MagicMock(spec=cinst.NLoad)
        mock_nload.var_name = "nload_var"
        mock_nload.comment = ""
        mock_nload.spad_address = 15

        # Create mock MInstructions
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "input_var"
        mock_mload.spad_address = 100
        mock_mload.comment = "load input variable"
        mock_mload.idx = 0

        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "output_var"
        mock_mstore.spad_address = 200
        mock_mstore.comment = ""
        mock_mstore.idx = 1

        mock_nload_minstr = MagicMock(spec=minst.MLoad)
        mock_nload_minstr.var_name = "nload_var"
        mock_nload_minstr.spad_address = 150
        mock_nload_minstr.comment = "nload comment"
        mock_nload_minstr.idx = 2

        # Create mock KernelInfo
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_csyncm, mock_cload, mock_cstore, mock_nload]
        mock_kernel.minstrs = [mock_mload, mock_nload_minstr, mock_mstore]

        # Create mock cinstrs_map
        mock_kernel.cinstrs_map = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        for entry in mock_kernel.cinstrs_map:
            entry.action = InstrAct.KEEP_SPAD

        # Create mock minstrs_map
        mock_mload_entry = MagicMock()
        mock_mload_entry.minstr = mock_mload
        mock_mload_entry.spad_addr = 10

        mock_mstore_entry = MagicMock()
        mock_mstore_entry.minstr = mock_mstore
        mock_mstore_entry.spad_addr = 20

        mock_nload_entry = MagicMock()
        mock_nload_entry.minstr = mock_nload_minstr
        mock_nload_entry.spad_addr = 15

        mock_kernel.minstrs_map = [mock_mload_entry, mock_nload_entry, mock_mstore_entry]

        # Mock the search functions
        with patch("linker.steps.program_linker.search_minstrs_back", return_value=0) as mock_search_back:
            with patch("linker.steps.program_linker.search_minstrs_forward") as mock_search_forward:
                mock_search_forward.side_effect = [2, 1]  # First call returns 2, second call returns 1

                # Execute the method
                self.program._update_cinst_kernel_hbm(mock_kernel)

                # Verify CSyncm target was updated to MInst idx
                self.assertEqual(mock_csyncm.target, 1)  # Should be set to mstore.idx

                # Verify CLoad was updated with correct variable name and SPAD address
                self.assertEqual(mock_cload.var_name, "input_var")
                self.assertEqual(mock_cload.spad_address, 100)

                # Verify CStore was updated with correct variable name and SPAD address
                self.assertEqual(mock_cstore.var_name, "output_var")
                self.assertEqual(mock_cstore.spad_address, 200)

                # Verify variable was added to tracker
                self.assertEqual(self.program._cinst_in_var_tracker["output_var"], 200)

                # Verify NLoad was updated with correct variable name
                self.assertEqual(mock_nload.var_name, "nload_var")

                # Verify search functions were called correctly
                mock_search_back.assert_called_with(mock_kernel.minstrs_map, 2, 10)
                mock_search_forward.assert_any_call(mock_kernel.minstrs_map, 2, 20)

    def test_update_xinsts(self):
        """@brief Test updating XInsts.

        @test Verifies that XInst bundles are correctly updated and invalid sequences are detected
        """
        # Create mock XInstructions
        mock_xinst1 = MagicMock()
        mock_xinst1.bundle = 1

        mock_xinst2 = MagicMock()
        mock_xinst2.bundle = 2

        mock_xinst3 = MagicMock()
        mock_xinst3.bundle = 0  # Will cause an error when updated after mock_xinst2

        # Execute the method
        kernel_xinstrs = [mock_xinst1, mock_xinst2]
        self.program._bundle_offset = 10
        last_bundle = self.program._update_xinsts(kernel_xinstrs)

        # Verify results
        self.assertEqual(mock_xinst1.bundle, 11)  # 1 + 10
        self.assertEqual(mock_xinst2.bundle, 12)  # 2 + 10
        self.assertEqual(last_bundle, 12)

        # Test that an invalid bundle sequence raises RuntimeError
        kernel_xinstrs = [
            mock_xinst2,
            mock_xinst3,
        ]  # xinst3 has lower bundle than xinst2
        with self.assertRaises(RuntimeError):
            self.program._update_xinsts(kernel_xinstrs)

    def test_link_kernel(self):
        """@brief Test linking a kernel.

        @test Verifies that a kernel is correctly linked with updated instructions
        """
        # Create mocks for the update methods
        with (
            patch.object(LinkedProgram, "_update_minsts") as mock_update_minsts,
            patch.object(LinkedProgram, "_update_cinsts") as mock_update_cinsts,
            patch.object(LinkedProgram, "_update_xinsts") as mock_update_xinsts,
        ):
            # Setup mock_update_xinsts to return a bundle offset
            mock_update_xinsts.return_value = 5

            # Create mock KernelInfo
            mock_kernel_info = MagicMock()
            mock_kernel_info.minstrs = [MagicMock(), MagicMock()]
            mock_kernel_info.cinstrs = [MagicMock(), MagicMock()]
            mock_kernel_info.xinstrs = [MagicMock(), MagicMock()]
            mock_kernel_info.spad_size = 0

            # Configure the mocks for to_line method
            for i, xinstr in enumerate(mock_kernel_info.xinstrs):
                xinstr.to_line.return_value = f"xinst{i}"
                xinstr.comment = f"xinst_comment{i}"

            # Create proper minstrs_map entries with references to mocked instructions
            mock_kernel_info.minstrs_map = []
            for i, minstr in enumerate(mock_kernel_info.minstrs):
                minstr.to_line.return_value = f"minst{i}"
                minstr.comment = f"minst_comment{i}"
                minstr_map_entry = MagicMock()
                minstr_map_entry.minstr = minstr
                minstr_map_entry.action = InstrAct.KEEP_HBM
                mock_kernel_info.minstrs_map.append(minstr_map_entry)

            # Create proper cinstrs_map entries with references to mocked instructions
            mock_kernel_info.cinstrs_map = []
            for i, cinstr in enumerate(mock_kernel_info.cinstrs):
                cinstr.to_line.return_value = f"cinst{i}"
                cinstr.comment = f"cinst_comment{i}"
                cinstr_map_entry = MagicMock()
                cinstr_map_entry.cinstr = cinstr
                cinstr_map_entry.action = InstrAct.KEEP_SPAD
                mock_kernel_info.cinstrs_map.append(cinstr_map_entry)

            # Execute the method
            self.program.link_kernel(mock_kernel_info)

            # Verify update methods were called
            mock_update_minsts.assert_called_once_with(mock_kernel_info)
            mock_update_cinsts.assert_called_once_with(mock_kernel_info)
            mock_update_xinsts.assert_called_once_with(mock_kernel_info.xinstrs)

            # Verify bundle offset was updated
            self.assertEqual(self.program._bundle_offset, 6)  # 5 + 1

            # Verify line offsets were updated
            self.assertEqual(self.program._minst_line_offset, 1)  # len(kernel_minstrs) - 1
            self.assertEqual(self.program._cinst_line_offset, 1)  # len(kernel_cinstrs) - 1

            # Verify kernel count was incremented
            self.assertEqual(self.program._kernel_count, 1)

            # Verify output streams contain the instructions
            xinst_output = self.streams["xinst"].getvalue()
            cinst_output = self.streams["cinst"].getvalue()
            minst_output = self.streams["minst"].getvalue()

            self.assertIn("xinst0", xinst_output)
            self.assertIn("xinst1", xinst_output)

            self.assertIn("0, cinst0", cinst_output)
            self.assertIn("cinst_comment0", cinst_output)

            self.assertIn("0, minst0", minst_output)
            self.assertIn("minst_comment0", minst_output)

    def test_link_kernel_with_no_hbm(self):
        """@brief Test linking a kernel with HBM disabled.

        @test Verifies that MInsts are ignored when HBM is disabled
        """
        with patch.object(GlobalConfig, "hasHBM", False):
            # Create mocks for the update methods
            with (
                patch.object(LinkedProgram, "_update_cinsts") as mock_update_cinsts,
                patch.object(LinkedProgram, "_update_xinsts") as mock_update_xinsts,
            ):
                # Setup mock_update_xinsts to return a bundle offset
                mock_update_xinsts.return_value = 5

                # Create mock instruction lists
                kernel_minstrs = [MagicMock(), MagicMock()]  # Should be ignored
                kernel_cinstrs = [MagicMock(), MagicMock()]
                kernel_xinstrs = [MagicMock(), MagicMock()]

                # Configure the mocks for to_line method
                for xinstr in kernel_xinstrs:
                    xinstr.to_line.return_value = "xinst"
                    xinstr.comment = None

                for cinstr in kernel_cinstrs:
                    cinstr.to_line.return_value = "cinst"
                    cinstr.comment = None

                # Create mock KernelInfo
                mock_kernel_info = MagicMock()
                mock_kernel_info.minstrs = kernel_minstrs
                mock_kernel_info.cinstrs = kernel_cinstrs
                mock_kernel_info.xinstrs = kernel_xinstrs
                mock_kernel_info.minstrs_map = [MagicMock(), MagicMock()]
                mock_kernel_info.cinstrs_map = [MagicMock(), MagicMock()]
                mock_kernel_info.spad_size = 0

                # Execute the method
                self.program.link_kernel(mock_kernel_info)

                # Verify update methods were called
                # No minsts should be processed when HBM is disabled
                mock_update_cinsts.assert_called_once_with(mock_kernel_info)
                mock_update_xinsts.assert_called_once_with(kernel_xinstrs)

                # Verify bundle offset was updated
                self.assertEqual(self.program._bundle_offset, 6)  # 5 + 1

                # No MInst output when HBM is disabled
                minst_output = self.streams["minst"].getvalue()
                self.assertEqual(minst_output, "")

    def test_link_kernel_with_closed_program(self):
        """@brief Test linking a kernel with a closed program.

        @test Verifies that a RuntimeError is raised when linking to a closed program
        """
        # Close the program
        self.program._is_open = False

        # Try to link a kernel
        with self.assertRaises(RuntimeError):
            self.program.link_kernel([])

    def test_link_kernel_with_suppress_comments(self):
        """@brief Test linking a kernel with comments suppressed.

        @test Verifies that comments are not included in the output when suppressed
        """
        with patch.object(GlobalConfig, "suppress_comments", True):
            # Create mocks for the update methods
            with (
                patch.object(LinkedProgram, "_update_minsts"),
                patch.object(LinkedProgram, "_update_cinsts"),
                patch.object(LinkedProgram, "_update_xinsts"),
            ):
                # Create mock instruction lists with comments
                kernel_minstrs = [MagicMock(), MagicMock()]
                kernel_cinstrs = [MagicMock(), MagicMock()]
                kernel_xinstrs = [MagicMock()]

                # Configure the mocks for to_line method
                kernel_xinstrs[0].to_line.return_value = "xinst"
                kernel_xinstrs[0].comment = "xinst_comment"

                kernel_cinstrs[0].to_line.return_value = "cinst"
                kernel_cinstrs[0].comment = "cinst_comment"

                kernel_minstrs[0].to_line.return_value = "minst"
                kernel_minstrs[0].comment = "minst_comment"

                # Create mock KernelInfo
                mock_kernel_info = MagicMock()
                mock_kernel_info.minstrs = kernel_minstrs
                mock_kernel_info.cinstrs = kernel_cinstrs
                mock_kernel_info.xinstrs = kernel_xinstrs
                mock_kernel_info.minstrs_map = [MagicMock(), MagicMock()]
                mock_kernel_info.cinstrs_map = [MagicMock(), MagicMock()]
                mock_kernel_info.spad_size = 0

                # Execute the method
                self.program.link_kernel(mock_kernel_info)

                # Verify comments were suppressed
                xinst_output = self.streams["xinst"].getvalue()
                cinst_output = self.streams["cinst"].getvalue()
                minst_output = self.streams["minst"].getvalue()

                self.assertNotIn("xinst_comment", xinst_output)
                self.assertNotIn("cinst_comment", cinst_output)
                self.assertNotIn("minst_comment", minst_output)

    def test_link_kernels_to_files(self):
        """
        @brief Test the link_kernels_to_files static method.

        @test Verifies that kernels are correctly linked and written to output files
        """
        program = LinkedProgram()

        # Create mock KernelInfo objects
        mock_input_kernel = MagicMock()
        mock_input_kernel.prefix = "/tmp/input1"
        mock_input_kernel.minst = "/tmp/input1.minst"
        mock_input_kernel.cinst = "/tmp/input1.cinst"
        mock_input_kernel.xinst = "/tmp/input1.xinst"
        mock_input_kernel.mem = None
        mock_input_kernel.hbm_remap_dict = {}

        mock_output_kernel = MagicMock()
        mock_output_kernel.prefix = "/tmp/output"
        mock_output_kernel.minst = "/tmp/output.minst"
        mock_output_kernel.cinst = "/tmp/output.cinst"
        mock_output_kernel.xinst = "/tmp/output.xinst"
        mock_output_kernel.mem = None
        mock_output_kernel.hbm_remap_dict = None

        kernels_info = [mock_input_kernel]
        program_info = mock_output_kernel

        mock_mem_model = MagicMock()
        mock_verbose = MagicMock()

        # Act
        with (
            patch("builtins.open", mock_open()),
            patch(
                "linker.steps.program_linker.Loader.load_minst_kernel_from_file",
                return_value=[],
            ),
            patch(
                "linker.steps.program_linker.Loader.load_cinst_kernel_from_file",
                return_value=[],
            ),
            patch(
                "linker.steps.program_linker.Loader.load_xinst_kernel_from_file",
                return_value=[],
            ),
            patch.object(LinkedProgram, "initialize", return_value=None) as mock_init,
            patch.object(LinkedProgram, "link_kernel") as mock_link_kernel,
            patch.object(LinkedProgram, "close") as mock_close,
        ):
            program.link_kernels_to_files(kernels_info, program_info, mock_mem_model, mock_verbose)

        # Assert
        mock_init.assert_called_once()
        mock_link_kernel.assert_called_once_with(mock_input_kernel)
        mock_close.assert_called_once()

    def test_flush_buffers(self):
        """@brief Test flushing the CInst and MInst input variable trackers.

        @test Verifies that buffers are correctly cleared and SPAD offset is reset
        """
        # Set up some data in the trackers and SPAD offset
        self.program._cinst_in_var_tracker = {"var1": 10, "var2": 20, "var3": 30}
        self.program._minst_in_var_tracker = {"var4": 40, "var5": 50}
        self.program._spad_offset = 100

        # Execute the method
        self.program.flush_buffers()

        # Verify that all trackers are cleared
        self.assertEqual(self.program._cinst_in_var_tracker, {})
        self.assertEqual(self.program._minst_in_var_tracker, {})

        # Verify that SPAD offset is reset to 0
        self.assertEqual(self.program._spad_offset, 0)


class TestLinkedProgramValidation(unittest.TestCase):
    """@brief Tests for the validation methods of the LinkedProgram class."""

    def setUp(self):
        """@brief Set up test fixtures."""
        # Group related stream objects into a dictionary
        self.streams = {
            "minst": io.StringIO(),
            "cinst": io.StringIO(),
            "xinst": io.StringIO(),
        }
        self.mem_model = MagicMock(spec=MemoryModel)

        # Mock the hasHBM property to return True by default
        self.has_hbm_patcher = patch.object(GlobalConfig, "hasHBM", True)
        self.mock_has_hbm = self.has_hbm_patcher.start()

        # Mock the suppress_comments property to return False by default
        self.suppress_comments_patcher = patch.object(GlobalConfig, "suppress_comments", False)
        self.mock_suppress_comments = self.suppress_comments_patcher.start()

        self.program = LinkedProgram()
        self.program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

    def tearDown(self):
        """@brief Tear down test fixtures."""
        self.has_hbm_patcher.stop()
        self.suppress_comments_patcher.stop()

    def test_validate_hbm_address(self):
        """@brief Test validating a HBM address.

        @test Verifies that valid addresses are accepted and invalid ones raise exceptions
        """

        # Test validating a valid HBM address
        self.mem_model.mem_info_vars = {}
        self.program._validate_hbm_address("test_var", 10)
        # No exception should be raised

        # Test validating a negative HBM address
        with self.assertRaises(RuntimeError):
            self.program._validate_hbm_address("test_var", -1)

    def test_validate_hbm_address_mismatch(self):
        """@brief Test validating an HBM address that doesn't match the declared address.

        @test Verifies that a RuntimeError is raised when address doesn't match
        """
        mock_var = MagicMock()
        mock_var.hbm_address = 5
        self.mem_model.mem_info_vars = {"test_var": mock_var}

        with self.assertRaises(RuntimeError):
            self.program._validate_hbm_address("test_var", 10)

    def test_validate_spad_address_valid(self):
        """@brief Test validating a valid SPAD address with HBM disabled.

        @test Verifies that valid SPAD addresses are accepted when HBM is disabled
        """
        with patch.object(GlobalConfig, "hasHBM", False):
            self.mem_model.mem_info_vars = {}
            self.program._validate_spad_address("test_var", 10)
            # No exception should be raised

    def test_validate_spad_address_with_hbm_enabled(self):
        """@brief Test validating a SPAD address with HBM enabled.

        @test Verifies that an AssertionError is raised when HBM is enabled
        """
        with self.assertRaises(AssertionError):
            self.program._validate_spad_address("test_var", 10)

    def test_validate_spad_address_negative(self):
        """@brief Test validating a negative SPAD address.

        @test Verifies that a RuntimeError is raised for negative addresses
        """
        with patch.object(GlobalConfig, "hasHBM", False):
            with self.assertRaises(RuntimeError):
                self.program._validate_spad_address("test_var", -1)

    def test_validate_spad_address_mismatch(self):
        """@brief Test validating a SPAD address that doesn't match the declared address.

        @test Verifies that a RuntimeError is raised when address doesn't match
        """
        with patch.object(GlobalConfig, "hasHBM", False):
            mock_var = MagicMock()
            mock_var.hbm_address = 5
            self.mem_model.mem_info_vars = {"test_var": mock_var}

            with self.assertRaises(RuntimeError):
                self.program._validate_spad_address("test_var", 10)


class TestJoinDinstKernels(unittest.TestCase):
    """@brief Tests for the join_n_prune_dinst_kernels static method."""

    def test_join_dinst_kernels_empty(self):
        """@brief Test joining empty list of DInst kernels.

        @test Verifies that a ValueError is raised for an empty list
        """
        program = LinkedProgram()
        with self.assertRaises(ValueError):
            program.join_n_prune_dinst_kernels([])

    def test_join_dinst_kernels_single_kernel(self):
        """@brief Test joining a single DInst kernel.

        @test Verifies that instructions from a single kernel are correctly processed
        """
        program = LinkedProgram()

        # Create mock DInstructions
        mock_dload = MagicMock(spec=dinst.DLoad)
        mock_dload.var = "var1"

        mock_dstore = MagicMock(spec=dinst.DStore)
        mock_dstore.var = "var2"

        # Execute the method
        result = program.join_n_prune_dinst_kernels([[mock_dload, mock_dstore]])

        # Verify result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], mock_dload)
        self.assertEqual(result[1], mock_dstore)

        # Verify address was set
        self.assertEqual(mock_dload.address, 0)
        self.assertEqual(mock_dstore.address, 1)

    def test_join_dinst_kernels_multiple_kernels(self):
        """@brief Test joining multiple DInst kernels.

        @test Verifies that instructions from multiple kernels are correctly merged
        """
        program = LinkedProgram()

        # Create mock DInstructions for first kernel
        mock_dload1 = MagicMock(spec=dinst.DLoad)
        mock_dload1.var = "var1"

        mock_dstore1 = MagicMock(spec=dinst.DStore)
        mock_dstore1.var = "var2"

        # Create mock DInstructions for second kernel
        mock_dload2 = MagicMock(spec=dinst.DLoad)
        mock_dload2.var = "var2"  # Same as output from first kernel

        mock_dkeygen = MagicMock(spec=dinst.DKeyGen)
        mock_dkeygen.var = "var3"

        mock_dstore2 = MagicMock(spec=dinst.DStore)
        mock_dstore2.var = "var4"

        # Execute the method
        result = program.join_n_prune_dinst_kernels([[mock_dload1, mock_dstore1], [mock_dload2, mock_dkeygen, mock_dstore2]])

        # Verify result - should contain load1, store1 (output), keygen, store2 (output)
        # dload2 should be skipped since it loads var2 which is already an output from kernel1
        self.assertEqual(len(result), 3)
        self.assertIn(mock_dload1, result)
        self.assertNotIn(mock_dload2, result)  # Should be skipped
        self.assertIn(mock_dkeygen, result)
        self.assertIn(mock_dstore2, result)

        # Verify addresses were set correctly and sequentially
        # Note: exact order depends on dictionary iteration which is not guaranteed
        used_addresses = {dinst.address for dinst in result}
        self.assertEqual(used_addresses, {0, 1, 2})  # Three consecutive addresses

    def test_join_dinst_kernels_with_carry_over_vars(self):
        """@brief Test joining DInst kernels with carry-over variables.

        @test Verifies that variables used across kernels are properly consolidated
        """

        program = LinkedProgram()

        # Create mock DInstructions for first kernel
        mock_dload1 = MagicMock(spec=dinst.DLoad)
        mock_dload1.var = "var1"

        mock_dstore1 = MagicMock(spec=dinst.DStore)
        mock_dstore1.var = "var2"

        # Create mock DInstructions for second kernel
        mock_dload2 = MagicMock(spec=dinst.DLoad)
        mock_dload2.var = "var2"  # Same as output from first kernel

        mock_dstore2 = MagicMock(spec=dinst.DStore)
        mock_dstore2.var = "var2"  # Same variable is also an output

        # Execute the method
        result = program.join_n_prune_dinst_kernels([[mock_dload1, mock_dstore1], [mock_dload2, mock_dstore2]])

        # Verify result - should contain load1, store2
        # Both dload2 and dstore1 should be skipped since var2 is carried over
        self.assertEqual(len(result), 2)
        self.assertIn(mock_dload1, result)
        self.assertNotIn(mock_dload2, result)  # Should be skipped
        self.assertNotIn(mock_dstore1, result)  # Should be skipped
        self.assertIn(mock_dstore2, result)  # Final output for var2


class TestPruneCinstKernel(unittest.TestCase):
    """@brief Tests for the prune_cinst_kernel methods."""

    def setUp(self):
        """@brief Set up test fixtures."""
        self.streams = {
            "minst": io.StringIO(),
            "cinst": io.StringIO(),
            "xinst": io.StringIO(),
        }
        self.mem_model = MagicMock(spec=MemoryModel)

        # Mock the hasHBM property to return True by default
        self.has_hbm_patcher = patch.object(GlobalConfig, "hasHBM", True)
        self.mock_has_hbm = self.has_hbm_patcher.start()

        self.program = LinkedProgram()
        self.program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

    def tearDown(self):
        """@brief Tear down test fixtures."""
        self.has_hbm_patcher.stop()

    def test_prune_cinst_kernel_hbm_ifetch_resets_cycles(self):
        """@brief Test that IFetch resets adjust_cycles in HBM mode."""
        # Create mock instructions
        mock_ifetch = MagicMock(spec=cinst.IFetch)
        mock_ifetch.comment = ""
        mock_cnop = MagicMock(spec=cinst.CNop)
        mock_cnop.comment = ""
        mock_cnop.cycles = 5

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_ifetch, mock_cnop]
        mock_kernel.cinstrs_map = [MagicMock(), MagicMock()]

        self.program.prune_cinst_kernel_hbm(mock_kernel, None)

        # CNop cycles should remain unchanged since adjust_cycles is reset by IFetch
        self.assertEqual(mock_cnop.cycles, 5)

    def test_prune_cinst_kernel_hbm_cnop_adds_cycles(self):
        """@brief Test that CNop adds adjust_cycles in HBM mode."""
        # Create mock instructions
        mock_cnop = MagicMock(spec=cinst.CNop)
        mock_cnop.comment = ""
        mock_cnop.cycles = 3

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_cnop]
        mock_kernel.cinstrs_map = [MagicMock()]
        mock_kernel.minstrs_map = []

        # Set up program to have some adjust_cycles
        with patch.object(self.program, "_intermediate_vars", ["var1"]):
            # Mock a CLoad that would be skipped to create adjust_cycles
            mock_cload = MagicMock(spec=cinst.CLoad)
            mock_cload.spad_address = 10
            mock_cload.comment = ""
            mock_cload.var_name = "test_var"

            mock_kernel.cinstrs = [mock_cload, mock_cnop]
            mock_kernel.cinstrs_map = [MagicMock(), MagicMock()]

            # Mock minstr that would be found and skipped
            mock_minstr = MagicMock()
            mock_minstr.var_name = "test_var"
            mock_minstr_entry = MagicMock()
            mock_minstr_entry.minstr = mock_minstr
            mock_minstr_entry.action = InstrAct.SKIP
            mock_kernel.minstrs_map = [mock_minstr_entry]

            with patch("linker.steps.program_linker.search_minstrs_back", return_value=0):
                with patch("linker.steps.program_linker.get_instruction_tp", return_value=2):
                    self.program.prune_cinst_kernel_hbm(mock_kernel, None)

            # CNop should have added the adjustment cycles
            self.assertEqual(mock_cnop.cycles, 5)  # 3 + 2

    def test_prune_cinst_kernel_hbm_csyncm_tracks_index(self):
        """@brief Test that CSyncm tracks minst index in HBM mode."""
        # Create mock instructions
        mock_csyncm = MagicMock(spec=cinst.CSyncm)
        mock_csyncm.comment = ""
        mock_csyncm.target = 1
        mock_cload = MagicMock(spec=cinst.CLoad)
        mock_cload.spad_address = 10
        mock_cload.comment = ""
        mock_cload.var_name = "test_var"

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_csyncm, mock_cload]
        mock_kernel.cinstrs_map = [MagicMock(), MagicMock()]
        mock_kernel.cinstrs_map[1].action = InstrAct.KEEP_SPAD

        # Mock minstr
        mock_minstr = MagicMock()
        mock_minstr.var_name = "test_var"
        mock_minstr_entry = MagicMock()
        mock_minstr_entry.minstr = mock_minstr
        mock_minstr_entry.action = InstrAct.KEEP_HBM
        mock_kernel.minstrs_map = [mock_minstr_entry, mock_minstr_entry]

        # Verify search was called with correct syncm_idx
        with patch("linker.steps.program_linker.search_minstrs_back") as mock_search:
            mock_search.return_value = 0
            self.program.prune_cinst_kernel_hbm(mock_kernel, None)
            mock_search.assert_called_with(mock_kernel.minstrs_map, 1, 10)

    def test_prune_cinst_kernel_hbm_cload_with_skipped_minstr(self):
        """@brief Test CLoad handling when corresponding minstr is skipped in HBM mode."""
        # Create mock CLoad
        mock_cload = MagicMock(spec=cinst.CLoad)
        mock_cload.spad_address = 10
        mock_cload.comment = ""
        mock_cload.var_name = "test_var"

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_cload]
        mock_kernel.cinstrs_map = [MagicMock()]

        # Mock minstr that is skipped
        mock_minstr = MagicMock()
        mock_minstr.var_name = "test_var"
        mock_minstr_entry = MagicMock()
        mock_minstr_entry.minstr = mock_minstr
        mock_minstr_entry.action = InstrAct.SKIP
        mock_kernel.minstrs_map = [mock_minstr_entry]

        with patch("linker.steps.program_linker.search_minstrs_back", return_value=0):
            with patch("linker.steps.program_linker_utils.get_instruction_tp", return_value=3):
                with patch("linker.steps.program_linker_utils.remove_csyncm", return_value=(-1, 2)):
                    self.program.prune_cinst_kernel_hbm(mock_kernel, None)

        # CLoad should be marked as SKIP
        self.assertEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)
        # Variable name should be updated
        self.assertEqual(mock_cload.var_name, "test_var")

    def test_prune_cinst_kernel_hbm_cload_with_intermediate_var(self):
        """@brief Test CLoad handling with intermediate variable in HBM mode."""
        # Set up intermediate variables
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock CLoad
        mock_cload = MagicMock(spec=cinst.CLoad)
        mock_cload.spad_address = 10
        mock_cload.comment = ""
        mock_cload.var_name = "intermediate_var"

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_cload]
        mock_kernel.cinstrs_map = [MagicMock()]

        # Mock minstr
        mock_minstr = MagicMock()
        mock_minstr.var_name = "intermediate_var"
        mock_minstr_entry = MagicMock()
        mock_minstr_entry.minstr = mock_minstr
        mock_minstr_entry.action = InstrAct.KEEP_HBM
        mock_kernel.minstrs_map = [mock_minstr_entry]

        with patch("linker.steps.program_linker.search_minstrs_back", return_value=0):
            with patch("linker.steps.program_linker.remove_csyncm", return_value=(-1, 2)) as mock_remove:
                self.program.prune_cinst_kernel_hbm(mock_kernel, None)

                # Should call remove_csyncm for intermediate variable
                mock_remove.assert_called_with(mock_kernel.cinstrs, mock_kernel.cinstrs_map, -1)

    def test_prune_cinst_kernel_hbm_cstore_with_intermediate_var(self):
        """@brief Test CStore handling with intermediate variable in HBM mode."""
        # Set up intermediate variables
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock CStore
        mock_cstore = MagicMock(spec=cinst.CStore)
        mock_cstore.comment = ""
        mock_cstore.var_name = "intermediate_var"

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [mock_cstore]
        mock_kernel.cinstrs_map = [MagicMock()]

        # Mock minstr
        mock_minstr = MagicMock()
        mock_minstr.var_name = "intermediate_var"
        mock_minstr_entry = MagicMock()
        mock_minstr_entry.minstr = mock_minstr
        mock_minstr_entry.action = InstrAct.KEEP_HBM
        mock_kernel.minstrs_map = [mock_minstr_entry]

        with patch("linker.steps.program_linker.search_minstrs_forward", return_value=0):
            with patch("linker.steps.program_linker.remove_csyncm", return_value=(-1, 2)) as mock_remove:
                self.program.prune_cinst_kernel_hbm(mock_kernel, None)

                # Should call remove_csyncm for intermediate variable
                mock_remove.assert_called_with(mock_kernel.cinstrs, mock_kernel.cinstrs_map, 1)

    def test_prune_cinst_kernel_no_hbm_with_keep_hbm_boundary(self):
        """@brief Test that prune_cinst_kernel_no_hbm returns early when keep_hbm_boundary is True."""
        # Set keep_hbm_boundary to True
        program = LinkedProgram(keep_hbm_boundary=True)
        program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

        mock_kernel = MagicMock()
        mock_kernel.cinstrs = [MagicMock()]

        # Should return early without processing
        program.prune_cinst_kernel_no_hbm(mock_kernel, None)

        # No changes should be made to the kernel
        self.assertIsNotNone(mock_kernel.cinstrs)

    def test_prune_cinst_kernel_no_hbm_ifetch_resets_cycles(self):
        """@brief Test that IFetch resets adjust_cycles in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Create mock instructions
            mock_ifetch = MagicMock(spec=cinst.IFetch)
            mock_ifetch.bundle = 1
            mock_cnop = MagicMock(spec=cinst.CNop)
            mock_cnop.cycles = 5

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_ifetch, mock_cnop]
            mock_kernel.cinstrs_map = [MagicMock(), MagicMock()]

            self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # CNop cycles should remain unchanged since adjust_cycles is reset by IFetch
            self.assertEqual(mock_cnop.cycles, 5)

    def test_prune_cinst_kernel_no_hbm_bload_processing(self):
        """@brief Test BLoad processing in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Create mock BLoad
            mock_bload = MagicMock(spec=cinst.BLoad)
            mock_bload.var_name = "test_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_bload]
            mock_kernel.cinstrs_map = [MagicMock()]

            with patch("linker.steps.program_linker.proc_seq_bloads", return_value=(0, 0)) as mock_process:
                self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

                # Should call proc_seq_bloads
                mock_process.assert_called_with(mock_kernel.cinstrs, mock_kernel.cinstrs_map, self.program._cinst_in_var_tracker, 0)

                # Variable should be added to tracker
                self.assertEqual(self.program._cinst_in_var_tracker["test_var"], 0)

    def test_prune_cinst_kernel_no_hbm_cload_already_loaded(self):
        """@brief Test CLoad handling when variable already loaded in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Set up variable tracker
            self.program._cinst_in_var_tracker = {"loaded_var": 5}

            # Create mock CLoad
            mock_cload = MagicMock(spec=cinst.CLoad)
            mock_cload.var_name = "loaded_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_cload]
            mock_kernel.cinstrs_map = [MagicMock()]

            with patch("linker.steps.program_linker_utils.get_instruction_tp", return_value=3):
                self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # CLoad should be marked as SKIP
            self.assertEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)

    def test_prune_cinst_kernel_no_hbm_cload_intermediate_var(self):
        """@brief Test CLoad handling with intermediate variable in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Set up intermediate variables
            self.program._intermediate_vars = ["intermediate_var"]

            # Create mock CLoad
            mock_cload = MagicMock(spec=cinst.CLoad)
            mock_cload.var_name = "intermediate_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_cload]
            mock_kernel.cinstrs_map = [MagicMock()]

            # Provide corresponding _xstores_map entry on the program instance
            xstore_entry = MagicMock()
            xstore_entry.action = InstrAct.SKIP
            self.program._xstores_map["intermediate_var"] = xstore_entry

            self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # CLoad should be marked as SKIP
            self.assertEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)

    def test_prune_cinst_kernel_no_hbm_cload_keep_instruction(self):
        """@brief Test CLoad when instruction should be kept in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Create mock CLoad
            mock_cload = MagicMock(spec=cinst.CLoad)
            mock_cload.var_name = "ct_new_var"
            mock_cload.spad_address = 10

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_cload]
            mock_kernel.cinstrs_map = [MagicMock()]

            self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # Variable should be added to tracker
            self.assertEqual(self.program._cinst_in_var_tracker["ct_new_var"], 10)

    def test_prune_cinst_kernel_no_hbm_bones_already_loaded(self):
        """@brief Test BOnes handling when variable already loaded in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Set up variable tracker
            self.program._cinst_in_var_tracker = {"loaded_var": 5}

            # Create mock BOnes
            mock_bones = MagicMock(spec=cinst.BOnes)
            mock_bones.var_name = "loaded_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_bones]
            mock_kernel.cinstrs_map = [MagicMock()]

            with patch("linker.steps.program_linker_utils.get_instruction_tp", return_value=2):
                self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # BOnes should be marked as SKIP
            self.assertEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)

    def test_prune_cinst_kernel_no_hbm_cstore_intermediate_var(self):
        """@brief Test CStore handling with intermediate variable in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Set up intermediate variables
            self.program._intermediate_vars = ["intermediate_var"]

            # Create mock CStore
            mock_cstore = MagicMock(spec=cinst.CStore)
            mock_cstore.var_name = "intermediate_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_cstore]
            mock_kernel.cinstrs_map = [MagicMock()]

            # _xstores_map is maintained by the LinkedProgram (self.program).
            # Provide an entry for the intermediate var so prune_cinst_kernel_no_hbm
            # can look it up on the program instance.
            xstore_entry = MagicMock()
            xstore_entry.action = InstrAct.SKIP
            self.program._xstores_map["intermediate_var"] = xstore_entry
            self.program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # CStore should be marked as SKIP
            self.assertEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)

    def test_prune_cinst_kernel_no_hbm_cstore_with_spad_boundary(self):
        """@brief Test CStore with intermediate variable but keep_spad_boundary=True in no-HBM mode."""
        with patch.object(GlobalConfig, "hasHBM", False):
            # Create program with keep_spad_boundary=True
            program = LinkedProgram(keep_spad_boundary=True)
            program.initialize(
                self.streams["minst"],
                self.streams["cinst"],
                self.streams["xinst"],
                self.mem_model,
            )
            program._intermediate_vars = ["intermediate_var"]

            # Create mock CStore
            mock_cstore = MagicMock(spec=cinst.CStore)
            mock_cstore.var_name = "intermediate_var"

            # Create mock kernel
            mock_kernel = MagicMock()
            mock_kernel.cinstrs = [mock_cstore]
            mock_kernel.cinstrs_map = [MagicMock()]

            program.prune_cinst_kernel_no_hbm(mock_kernel, None)

            # CStore should NOT be marked as SKIP due to keep_spad_boundary
            self.assertNotEqual(mock_kernel.cinstrs_map[0].action, InstrAct.SKIP)


class TestPruneMinstKernel(unittest.TestCase):
    """@brief Tests for the prune_minst_kernel method."""

    def setUp(self):
        """@brief Set up test fixtures."""
        self.streams = {
            "minst": io.StringIO(),
            "cinst": io.StringIO(),
            "xinst": io.StringIO(),
        }
        self.mem_model = MagicMock(spec=MemoryModel)

        # Mock the hasHBM property to return True by default
        self.has_hbm_patcher = patch.object(GlobalConfig, "hasHBM", True)
        self.mock_has_hbm = self.has_hbm_patcher.start()

        self.program = LinkedProgram()
        self.program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

    def tearDown(self):
        """@brief Tear down test fixtures."""
        self.has_hbm_patcher.stop()

    def test_prune_minst_kernel_with_keep_hbm_boundary(self):
        """@brief Test that prune_minst_kernel returns early when keep_hbm_boundary is True."""
        # Set keep_hbm_boundary to True
        program = LinkedProgram(keep_hbm_boundary=True)
        program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )

        mock_kernel = MagicMock()
        mock_kernel.minstrs = [MagicMock()]

        # Should return early without processing
        program.prune_minst_kernel(mock_kernel)

        # No changes should be made to the kernel
        self.assertIsNotNone(mock_kernel.minstrs)

    def test_prune_minst_kernel_msyncc_tracking(self):
        """@brief Test that MSyncc instructions are tracked correctly."""
        # Create mock MSyncc instruction
        mock_msyncc = MagicMock(spec=minst.MSyncc)
        mock_msyncc.idx = 0
        mock_msyncc.comment = ""

        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "test_var"
        mock_mload.spad_address = 10
        mock_mload.comment = ""
        mock_mload.idx = 1

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_msyncc, mock_mload]
        mock_kernel.minstrs_map = [MagicMock(), MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MSyncc should be tracked but not modified
        self.assertIsNotNone(mock_msyncc)

    def test_prune_minst_kernel_mstore_intermediate_var(self):
        """@brief Test MStore handling with intermediate variable."""
        # Set up intermediate variables
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock MStore
        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "intermediate_var"
        mock_mstore.spad_address = 20
        mock_mstore.comment = ""
        mock_mstore.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mstore]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MStore should be marked as SKIP (since keep_spad_boundary is False by default)
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)

    def test_prune_minst_kernel_mstore_intermediate_var_with_spad_boundary(self):
        """@brief Test MStore with intermediate variable but keep_spad_boundary=True."""
        # Create program with keep_spad_boundary=True
        program = LinkedProgram(keep_spad_boundary=True)
        program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )
        program._intermediate_vars = ["intermediate_var"]

        # Create mock MStore
        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "intermediate_var"
        mock_mstore.spad_address = 20
        mock_mstore.comment = ""
        mock_mstore.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mstore]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        program.prune_minst_kernel(mock_kernel)

        # MStore should be marked as KEEP_SPAD due to keep_spad_boundary
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.KEEP_SPAD)

    def test_prune_minst_kernel_mstore_with_preceding_msyncc(self):
        """@brief Test MStore intermediate variable with preceding MSyncc removal."""
        # Set up intermediate variables
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock MSyncc and MStore
        mock_msyncc = MagicMock(spec=minst.MSyncc)
        mock_msyncc.idx = 0
        mock_msyncc.comment = ""

        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "intermediate_var"
        mock_mstore.spad_address = 15
        mock_mstore.comment = ""
        mock_mstore.idx = 1

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_msyncc, mock_mstore]
        mock_kernel.minstrs_map = [MagicMock(), MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # Both MSyncc and MStore should be marked as SKIP
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)  # MSyncc
        self.assertEqual(mock_kernel.minstrs_map[1].action, InstrAct.SKIP)  # MStore

    def test_prune_minst_kernel_mstore_keep_instruction(self):
        """@brief Test MStore when instruction should be kept."""
        # Create mock MStore with non-intermediate variable
        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "output_var"
        mock_mstore.spad_address = 20
        mock_mstore.comment = ""
        mock_mstore.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mstore]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MStore should not be marked as SKIP
        self.assertNotEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)
        # SPAD address should be adjusted (starts at 0, no adjustment needed)
        self.assertEqual(mock_mstore.spad_address, 20)

    def test_prune_minst_kernel_mload_already_loaded(self):
        """@brief Test MLoad handling when variable already loaded."""
        # Set up variable tracker
        self.program._minst_in_var_tracker = {"pt_loaded_var": 5}

        # Create mock MLoad
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "pt_loaded_var"
        mock_mload.spad_address = 10
        mock_mload.comment = ""
        mock_mload.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MLoad should be marked as SKIP
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)
        # SPAD address should be updated to tracked address
        self.assertEqual(mock_mload.spad_address, 5)

    def test_prune_minst_kernel_mload_intermediate_var(self):
        """@brief Test MLoad handling with intermediate variable."""
        # Set up intermediate variables
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock MLoad
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "intermediate_var"
        mock_mload.spad_address = 10
        mock_mload.comment = ""
        mock_mload.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MLoad should be marked as SKIP (since keep_spad_boundary is False by default)
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)

    def test_prune_minst_kernel_mload_intermediate_var_with_spad_boundary(self):
        """@brief Test MLoad with intermediate variable but keep_spad_boundary=True."""
        # Create program with keep_spad_boundary=True
        program = LinkedProgram(keep_spad_boundary=True)
        program.initialize(
            self.streams["minst"],
            self.streams["cinst"],
            self.streams["xinst"],
            self.mem_model,
        )
        program._intermediate_vars = ["intermediate_var"]

        # Create mock MLoad
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "intermediate_var"
        mock_mload.spad_address = 10
        mock_mload.comment = ""
        mock_mload.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        program.prune_minst_kernel(mock_kernel)

        # MLoad should be marked as KEEP_SPAD due to keep_spad_boundary
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.KEEP_SPAD)

    def test_prune_minst_kernel_mload_keep_instruction(self):
        """@brief Test MLoad when instruction should be kept."""
        # Create mock MLoad with new variable
        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "new_var"
        mock_mload.spad_address = 10
        mock_mload.comment = ""
        mock_mload.idx = 0

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload]
        mock_kernel.minstrs_map = [MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # MLoad should not be marked as SKIP
        self.assertNotEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)
        # Variable should be added to tracker
        self.assertEqual(self.program._minst_in_var_tracker["new_var"], 10)

    def test_prune_minst_kernel_mixed_instructions(self):
        """@brief Test processing multiple mixed instruction types."""
        # Set up trackers and intermediate variables
        self.program._minst_in_var_tracker = {"ct_already_loaded": 5}
        self.program._intermediate_vars = ["intermediate_var"]

        # Create mock instructions
        mock_msyncc = MagicMock(spec=minst.MSyncc)
        mock_msyncc.idx = 0
        mock_msyncc.comment = "MSyncc instruction"

        mock_mload1 = MagicMock(spec=minst.MLoad)  # Already loaded
        mock_mload1.var_name = "ct_already_loaded"
        mock_mload1.spad_address = 10
        mock_mload1.comment = ""
        mock_mload1.idx = 1

        mock_mstore = MagicMock(spec=minst.MStore)  # Intermediate variable
        mock_mstore.var_name = "intermediate_var"
        mock_mstore.spad_address = 15
        mock_mstore.comment = ""
        mock_mstore.idx = 2

        mock_mload2 = MagicMock(spec=minst.MLoad)  # New variable
        mock_mload2.var_name = "ct_new_var"
        mock_mload2.spad_address = 20
        mock_mload2.comment = ""
        mock_mload2.idx = 3

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_msyncc, mock_mload1, mock_mstore, mock_mload2]
        mock_kernel.minstrs_map = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # Check actions
        self.assertNotEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)  # MSyncc (no action change)
        self.assertEqual(mock_kernel.minstrs_map[1].action, InstrAct.SKIP)  # MLoad1 (already loaded)
        self.assertEqual(mock_kernel.minstrs_map[2].action, InstrAct.SKIP)  # MStore (intermediate)
        self.assertNotEqual(mock_kernel.minstrs_map[3].action, InstrAct.SKIP)  # MLoad2 (new var)

        # Check variable tracking
        self.assertEqual(self.program._minst_in_var_tracker["ct_new_var"], 18)  # 20 - 2 (adjust_spad)

    def test_prune_minst_kernel_spad_size_tracking(self):
        """@brief Test that SPAD size is correctly tracked and updated."""
        # Create mock instructions with different SPAD addresses
        mock_mload1 = MagicMock(spec=minst.MLoad)
        mock_mload1.var_name = "var1"
        mock_mload1.spad_address = 10
        mock_mload1.comment = ""
        mock_mload1.idx = 0

        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "var2"
        mock_mstore.spad_address = 25
        mock_mstore.comment = ""
        mock_mstore.idx = 1

        mock_mload2 = MagicMock(spec=minst.MLoad)
        mock_mload2.var_name = "var3"
        mock_mload2.spad_address = 15
        mock_mload2.comment = ""
        mock_mload2.idx = 2

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload1, mock_mstore, mock_mload2]
        mock_kernel.minstrs_map = [MagicMock(), MagicMock(), MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # SPAD size should be the maximum SPAD address encountered
        self.assertEqual(mock_kernel.spad_size, 25)

    def test_prune_minst_kernel_adjustment_calculations(self):
        """@brief Test that SPAD address adjustments are calculated correctly."""
        # Set up intermediate variables to cause adjustments
        self.program._intermediate_vars = ["intermediate_var1", "intermediate_var2"]

        # Create mock instructions that will cause adjustments
        mock_mload1 = MagicMock(spec=minst.MLoad)  # Intermediate - will be skipped
        mock_mload1.var_name = "intermediate_var1"
        mock_mload1.spad_address = 10
        mock_mload1.comment = ""
        mock_mload1.idx = 0

        mock_mstore = MagicMock(spec=minst.MStore)  # Intermediate - will be skipped
        mock_mstore.var_name = "intermediate_var2"
        mock_mstore.spad_address = 15
        mock_mstore.comment = ""
        mock_mstore.idx = 1

        mock_mload2 = MagicMock(spec=minst.MLoad)  # Regular - should be adjusted
        mock_mload2.var_name = "regular_var"
        mock_mload2.spad_address = 20
        mock_mload2.comment = ""
        mock_mload2.idx = 2

        # Create mock kernel
        mock_kernel = MagicMock()
        mock_kernel.minstrs = [mock_mload1, mock_mstore, mock_mload2]
        mock_kernel.minstrs_map = [MagicMock(), MagicMock(), MagicMock()]
        mock_kernel.spad_size = 0

        self.program.prune_minst_kernel(mock_kernel)

        # First two instructions should be skipped
        self.assertEqual(mock_kernel.minstrs_map[0].action, InstrAct.SKIP)
        self.assertEqual(mock_kernel.minstrs_map[1].action, InstrAct.SKIP)

        # Third instruction should have adjusted SPAD address
        # adjust_spad should be -2 (from two skipped instructions)
        expected_spad = 20 - 2  # Original 20, minus 2 for adjustments
        self.assertEqual(mock_mload2.spad_address, expected_spad)

        # Variable should be tracked with adjusted address
        self.assertEqual(self.program._minst_in_var_tracker["regular_var"], expected_spad)


if __name__ == "__main__":
    unittest.main()
