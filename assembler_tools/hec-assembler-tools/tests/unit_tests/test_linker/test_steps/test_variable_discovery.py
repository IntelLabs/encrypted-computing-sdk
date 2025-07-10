# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the variable discovery module.
"""

import unittest
from unittest.mock import patch, MagicMock

from linker.steps.variable_discovery import discover_variables, discover_variables_spad


class TestVariableDiscovery(unittest.TestCase):
    """@brief Tests for the variable discovery functions."""

    def setUp(self):
        """@brief Set up test fixtures."""
        # Group MInstructions in a dictionary
        self.m_instrs = {
            "load": MagicMock(source="var1"),
            "store": MagicMock(dest="var2"),
            "other": MagicMock(),  # MInstruction that's neither MLoad nor MStore
        }

        # Group CInstructions in a dictionary
        self.c_instrs = {
            "bload": MagicMock(source="var3"),
            "cload": MagicMock(source="var4"),
            "bones": MagicMock(source="var5"),
            "nload": MagicMock(source="var6"),
            "cstore": MagicMock(dest="var7"),
            "other": MagicMock(),  # CInstruction that's none of the above
        }

    @patch("linker.steps.variable_discovery.minst")
    @patch("linker.steps.variable_discovery.MInstruction")
    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_valid(
        self, mock_validate, mock_minst_class, mock_minst
    ):
        """@brief Test discovering variables from valid MInstructions.

        @test Verifies that variables are correctly discovered from MLoad and MStore instructions
        """
        # Setup mocks
        mock_minst.MLoad = MagicMock()
        mock_minst.MStore = MagicMock()

        # Configure type checking at the module level, avoiding patching isinstance
        def is_minst_side_effect(obj):
            return obj in [
                self.m_instrs["load"],
                self.m_instrs["store"],
                self.m_instrs["other"],
            ]

        def is_mload_side_effect(obj):
            return obj is self.m_instrs["load"]

        def is_mstore_side_effect(obj):
            return obj is self.m_instrs["store"]

        # Replace the actual isinstance calls in the module with our mock functions
        with patch(
            "linker.steps.variable_discovery.isinstance",
            side_effect=lambda obj, cls: {
                mock_minst_class: is_minst_side_effect(obj),
                mock_minst.MLoad: is_mload_side_effect(obj),
                mock_minst.MStore: is_mstore_side_effect(obj),
            }.get(cls, False),
        ):

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

    @patch("linker.steps.variable_discovery.cinst")
    @patch("linker.steps.variable_discovery.CInstruction")
    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_spad_valid(
        self, mock_validate, mock_cinst_class, mock_cinst
    ):
        """@brief Test discovering variables from valid CInstructions.

        @test Verifies that variables are correctly discovered from all relevant CInstruction types
        """
        # Setup mocks
        mock_cinst.BLoad = MagicMock()
        mock_cinst.CLoad = MagicMock()
        mock_cinst.BOnes = MagicMock()
        mock_cinst.NLoad = MagicMock()
        mock_cinst.CStore = MagicMock()

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

        # Improved mock for isinstance that handles tuples of classes
        def mock_isinstance(obj, cls):
            # Handle tuple case first
            if isinstance(cls, tuple):
                return any(mock_isinstance(obj, c) for c in cls)

            # Use a dictionary to map class types to their respective checks
            class_checks = {
                mock_cinst_class: lambda: obj in cinstrs,
                mock_cinst.BLoad: lambda: obj is self.c_instrs["bload"],
                mock_cinst.CLoad: lambda: obj is self.c_instrs["cload"],
                mock_cinst.BOnes: lambda: obj is self.c_instrs["bones"],
                mock_cinst.NLoad: lambda: obj is self.c_instrs["nload"],
                mock_cinst.CStore: lambda: obj is self.c_instrs["cstore"],
            }

            # Check if cls is in our mapping and return the result of its check function
            return class_checks.get(cls, lambda: False)()

        # Patch the isinstance calls at the module level
        with patch(
            "linker.steps.variable_discovery.isinstance", side_effect=mock_isinstance
        ):
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
            self.assertIn("not a valid MInstruction", str(context.exception))

    @patch("linker.steps.variable_discovery.cinst")
    @patch("linker.steps.variable_discovery.CInstruction")
    @patch("assembler.memory_model.variable.Variable.validateName")
    def test_discover_variables_spad_invalid_variable_name(
        self, mock_validate, mock_cinst_class, mock_cinst
    ):
        """@brief Test discovering variables with an invalid variable name.

        @test Verifies that a RuntimeError is raised when a variable name is invalid
        """
        # Setup mocks
        mock_cinst.BLoad = MagicMock()

        # Configure validateName to return False
        mock_validate.return_value = False

        # Mock isinstance to make our mock object appear as CInstruction and BLoad
        with patch(
            "linker.steps.variable_discovery.isinstance",
            side_effect=lambda obj, cls: {
                mock_cinst_class: True,
                (
                    mock_cinst.BLoad,
                    mock_cinst.CLoad,
                    mock_cinst.BOnes,
                    mock_cinst.NLoad,
                ): True,
            }.get(cls, False),
        ):
            # Call the function
            with self.assertRaises(RuntimeError) as context:
                list(discover_variables_spad([self.c_instrs["bload"]]))

            # Verify the error message
            self.assertIn("Invalid Variable name", str(context.exception))


if __name__ == "__main__":
    unittest.main()
