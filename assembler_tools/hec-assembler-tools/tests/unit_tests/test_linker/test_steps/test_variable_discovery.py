# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the variable discovery module.
"""

import unittest
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest
from assembler.common.config import GlobalConfig
from linker.instructions.cinst import BLoad, BOnes, CLoad, CNop, CStore, NLoad
from linker.instructions.minst import MLoad, MStore, MSyncc
from linker.steps.variable_discovery import (
    check_unused_variables,
    discover_variables,
    discover_variables_spad,
    scan_variables,
)


class TestVariableDiscovery(unittest.TestCase):
    """@brief Tests for the variable discovery functions."""

    def setUp(self):
        """@brief Set up test fixtures."""
        # Group MInstructions in a dictionary
        self.m_instrs = {
            "load": MagicMock(source="var1", spec=MLoad),
            "store": MagicMock(dest="var2", spec=MStore),
            "other": MagicMock(spec=MSyncc),  # MInstruction that's neither MLoad nor MStore
        }

        # Group CInstructions in a dictionary
        self.c_instrs = {
            "bload": MagicMock(source="var3", spec=BLoad),
            "cload": MagicMock(source="var4", spec=CLoad),
            "bones": MagicMock(source="var5", spec=BOnes),
            "nload": MagicMock(source="var6", spec=NLoad),
            "cstore": MagicMock(dest="var7", spec=CStore),
            "other": MagicMock(spec=CNop),  # CInstruction that's none of the above
        }

    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_valid(self, mock_validate):
        """@brief Test discovering variables from valid MInstructions.

        @test Verifies that variables are correctly discovered from MLoad and MStore instructions
        """

        # Configure validateName to return True
        mock_validate.return_value = True

        # Test with a list containing both MLoad and MStore
        minstrs = [
            self.m_instrs["load"],
            self.m_instrs["store"],
            self.m_instrs["other"],
        ]

        # Call the function
        result = list(discover_variables(minstrs))

        # Verify results
        self.assertEqual(result, ["var1", "var2"])
        mock_validate.assert_any_call("var1")
        mock_validate.assert_any_call("var2")

    def test_discover_variables_empty_list(self):
        """@brief Test discovering variables from an empty list of MInstructions.

        @test Verifies that an empty list is returned when no instructions are provided
        """
        # No need to patch isinstance for an empty list
        result = list(discover_variables([]))

        # Verify results - should be an empty list
        self.assertEqual(result, [])

    def test_discover_variables_invalid_type(self):
        """@brief Test discovering variables with invalid types in the list.

        @test Verifies that a TypeError is raised when an invalid object is in the list
        """
        # Setup mock to fail the isinstance check
        invalid_obj = MagicMock()

        with patch("linker.steps.variable_discovery.isinstance", return_value=False):
            # Call the function with a list containing an invalid type
            with self.assertRaises(TypeError) as context:
                list(discover_variables([invalid_obj]))

            # Verify the error message
            self.assertIn("not a valid MInstruction", str(context.exception))

    @patch("linker.steps.variable_discovery.minst")
    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_invalid_variable_name(self, mock_validate, mock_minst):
        """@brief Test discovering variables with an invalid variable name.

        @test Verifies that a RuntimeError is raised when a variable name is invalid
        """
        # Setup mocks
        mock_minst.MLoad = MagicMock()

        # Configure validateName to return False
        mock_validate.return_value = False

        with patch(
            "linker.steps.variable_discovery.isinstance",
            side_effect=lambda obj, cls: True,
        ):
            # Call the function
            with self.assertRaises(RuntimeError) as context:
                list(discover_variables([self.m_instrs["load"]]))

            # Verify the error message
            self.assertIn("Invalid Variable name", str(context.exception))

    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_spad_valid(self, mock_validate):
        """@brief Test discovering variables from valid CInstructions.

        @test Verifies that variables are correctly discovered from all relevant CInstruction types
        """
        # Configure validateName to return True
        mock_validate.return_value = True

        # Test with a list containing all types of CInstructions
        cinstrs = [
            self.c_instrs["bload"],
            self.c_instrs["cload"],
            self.c_instrs["bones"],
            self.c_instrs["nload"],
            self.c_instrs["cstore"],
            self.c_instrs["other"],
        ]

        # Call the function
        result = list(discover_variables_spad(cinstrs))

        # Verify results
        self.assertEqual(result, ["var3", "var4", "var5", "var6", "var7"])
        mock_validate.assert_any_call("var3")
        mock_validate.assert_any_call("var4")
        mock_validate.assert_any_call("var5")
        mock_validate.assert_any_call("var6")
        mock_validate.assert_any_call("var7")

    def test_discover_variables_spad_empty_list(self):
        """@brief Test discovering variables from an empty list of CInstructions.

        @test Verifies that an empty list is returned when no instructions are provided
        """
        # Call the function with an empty list
        result = list(discover_variables_spad([]))

        # Verify results - should be an empty list
        self.assertEqual(result, [])

    def test_discover_variables_spad_invalid_type(self):
        """@brief Test discovering variables with invalid types in the list.

        @test Verifies that a TypeError is raised when an invalid object is in the list
        """
        # Setup mock
        invalid_obj = MagicMock()

        with patch("linker.steps.variable_discovery.isinstance", return_value=False):
            # Call the function with a list containing an invalid type
            with self.assertRaises(TypeError) as context:
                list(discover_variables_spad([invalid_obj]))

            # Verify the error message
            self.assertIn("not a valid CInstruction", str(context.exception))

    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_spad_invalid_variable_name(self, mock_validate):
        """@brief Test discovering variables with an invalid variable name.

        @test Verifies that a RuntimeError is raised when a variable name is invalid
        """

        # Configure validateName to return False
        mock_validate.return_value = False

        # Call the function
        with self.assertRaises(RuntimeError) as context:
            list(discover_variables_spad([self.c_instrs["bload"]]))

        # Verify the error message
        self.assertIn("Invalid Variable name", str(context.exception))

    def test_scan_variables(self):
        """
        @brief Test scan_variables function with and without HBM

        @test Verifies that scan_variables correctly processes input files and updates the memory model
              in both HBM and non-HBM modes
        """
        # Create a namedtuple similar to KernelInfo for testing
        KernelInfo = namedtuple(
            "KernelInfo",
            ["directory", "prefix", "minst", "cinst", "xinst", "mem", "remap_dict"],
        )
        input_files = [
            KernelInfo(
                directory="/tmp",
                prefix="input1",
                minst="/tmp/input1.minst",
                cinst="/tmp/input1.cinst",
                xinst="/tmp/input1.xinst",
                mem=None,
                remap_dict=None,
            )
        ]

        # Test with both True and False for hasHBM
        for has_hbm in [True, False]:
            with self.subTest(has_hbm=has_hbm):
                # Arrange
                GlobalConfig.hasHBM = has_hbm
                mock_mem_model = MagicMock()
                mock_verbose = MagicMock()

                # Act
                with (
                    patch(
                        "linker.steps.variable_discovery.Loader.load_minst_kernel_from_file",
                        return_value=[],
                    ),
                    patch(
                        "linker.steps.variable_discovery.Loader.load_cinst_kernel_from_file",
                        return_value=[],
                    ),
                    patch(
                        "linker.steps.variable_discovery.discover_variables",
                        return_value=["var1", "var2"],
                    ),
                    patch(
                        "linker.steps.variable_discovery.discover_variables_spad",
                        return_value=["var1", "var2"],
                    ),
                ):
                    scan_variables(input_files, mock_mem_model, mock_verbose)

                # Assert
                self.assertEqual(mock_mem_model.add_variable.call_count, 2)

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
            check_unused_variables(mock_mem_model)


if __name__ == "__main__":
    unittest.main()
