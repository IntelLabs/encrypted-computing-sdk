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

    def test_update_minsts(self):
        """@brief Test updating MInsts.

        @test Verifies that MInsts are correctly updated with offsets and variable addresses
        """
        # Create mock MInstructions
        mock_msyncc = MagicMock(spec=minst.MSyncc)
        mock_msyncc.target = 5

        mock_mload = MagicMock(spec=minst.MLoad)
        mock_mload.var_name = "input_var"
        mock_mload.hbm_address = 0
        mock_mload.comment = "original comment"

        mock_mstore = MagicMock(spec=minst.MStore)
        mock_mstore.var_name = "output_var"
        mock_mstore.hbm_address = 0
        mock_mstore.comment = ""

        # Set up memory model mock
        self.mem_model.use_variable.side_effect = [
            10,
            20,
        ]  # Return different addresses for different vars

        # Create mock CInstr for cinstrs_map
        mock_cinstr = MagicMock()
        mock_cinstr.idx = 5  # Same as msyncc.target

        # Create mock CinstrMapEntry
        mock_cinstr_map_entry = MagicMock()
        mock_cinstr_map_entry.cinstr = mock_cinstr

        # Create mock KernelInfo
        mock_kernel_info = MagicMock()
        mock_kernel_info.minstrs = [mock_msyncc, mock_mload, mock_mstore]
        mock_kernel_info.cinstrs_map = {5: mock_cinstr_map_entry}  # Map target 5 to mock entry
        mock_kernel_info.minstrs_map = [MagicMock(), MagicMock(), MagicMock()]

        # Configure minstrs_map actions
        for minstr_map in mock_kernel_info:
            minstr_map.action = MagicMock()  # Mock the action attribute

        # Execute the update
        self.program._cinst_line_offset = 10  # Set initial offset
        self.program._kernel_count = 1  # Set kernel count
        self.program._update_minsts(mock_kernel_info)

        # Verify results
        self.assertEqual(mock_msyncc.target, 15)  # 5 + 10
        self.assertEqual(mock_mload.hbm_address, 10)  # Replaced with HBM address
        self.assertIn("input_var", mock_mload.comment)  # Comment updated
        self.assertIn("original comment", mock_mload.comment)  # Original comment preserved

        self.assertEqual(mock_mstore.hbm_address, 20)  # Replaced with HBM address

        # Verify the memory model was used correctly
        self.mem_model.use_variable.assert_has_calls([call("input_var", 1), call("output_var", 1)])

    def test_remove_and_merge_csyncm_cnop(self):
        """@brief Test removing CSyncm instructions and merging CNop instructions.

        @test Verifies that CSyncm instructions are removed and CNop cycles are updated correctly
        """
        # Create mock CInstructions
        mock_ifetch = MagicMock(spec=cinst.IFetch)
        mock_ifetch.bundle = 1
        mock_ifetch.tokens = [0]

        mock_csyncm1 = MagicMock(spec=cinst.CSyncm)
        mock_csyncm1.tokens = [0]

        mock_cnop1 = MagicMock(spec=cinst.CNop)
        mock_cnop1.cycles = 2
        mock_cnop1.tokens = [0]

        mock_csyncm2 = MagicMock(spec=cinst.CSyncm)
        mock_csyncm2.tokens = [0]

        mock_cnop2 = MagicMock(spec=cinst.CNop)
        mock_cnop2.cycles = 3
        mock_cnop2.tokens = [0]

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
        kernel_cinstrs = [mock_ifetch, mock_csyncm]
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
            self.assertIn("xinst_comment0", xinst_output)

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


if __name__ == "__main__":
    unittest.main()
