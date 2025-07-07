# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
Unit tests for the loader module.
"""

import unittest
from unittest.mock import patch, mock_open, MagicMock, call

from linker.loader import (
    load_minst_kernel,
    load_minst_kernel_from_file,
    load_cinst_kernel,
    load_cinst_kernel_from_file,
    load_xinst_kernel,
    load_xinst_kernel_from_file,
    load_dinst_kernel,
    load_dinst_kernel_from_file,
)


class TestLoader(unittest.TestCase):
    """Tests for the loader module functions."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample instruction lines for each type
        self.minst_lines = ["MINST arg1, arg2", "MINST arg3, arg4"]
        self.cinst_lines = ["CINST arg1, arg2", "CINST arg3, arg4"]
        self.xinst_lines = ["XINST arg1, arg2", "XINST arg3, arg4"]
        self.dinst_lines = ["DINST arg1, arg2", "DINST arg3, arg4"]

        # Create mock instruction objects
        self.mock_minst = [MagicMock(), MagicMock()]
        self.mock_cinst = [MagicMock(), MagicMock()]
        self.mock_xinst = [MagicMock(), MagicMock()]
        self.mock_dinst = [MagicMock(), MagicMock()]

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.minst.factory")
    def test_load_minst_kernel_success(self, mock_factory, mock_create):
        """Test successful loading of MInstructions from an iterator."""
        # Configure mocks
        mock_factory.return_value = "minst_factory"
        mock_create.side_effect = self.mock_minst

        # Call the function
        result = load_minst_kernel(self.minst_lines)

        # Verify the results
        self.assertEqual(result, self.mock_minst)
        # Factory is called once per line, so 2 times total
        self.assertEqual(mock_factory.call_count, 2)
        self.assertEqual(mock_create.call_count, 2)
        mock_create.assert_has_calls(
            [
                call(self.minst_lines[0], "minst_factory"),
                call(self.minst_lines[1], "minst_factory"),
            ]
        )

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.minst.factory")
    def test_load_minst_kernel_failure(self, mock_factory, mock_create):
        """Test error handling when loading MInstructions fails."""
        # Configure mocks
        mock_factory.return_value = "minst_factory"
        mock_create.return_value = None

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_minst_kernel(self.minst_lines)

        self.assertIn(
            f"Error parsing line 1: {self.minst_lines[0]}", str(context.exception)
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_minst_kernel")
    def test_load_minst_kernel_from_file_success(self, mock_load, mock_file):
        """Test successful loading of MInstructions from a file."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.minst_lines
        mock_load.return_value = self.mock_minst

        # Call the function
        result = load_minst_kernel_from_file("test.minst")

        # Verify the results
        self.assertEqual(result, self.mock_minst)
        mock_file.assert_called_once_with("test.minst", "r")
        mock_load.assert_called_once_with(self.minst_lines)

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_minst_kernel")
    def test_load_minst_kernel_from_file_failure(self, mock_load, mock_file):
        """Test error handling when loading MInstructions from a file fails."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.minst_lines
        mock_load.side_effect = Exception("Test error")

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_minst_kernel_from_file("test.minst")

        self.assertIn(
            'Error occurred loading file "test.minst"', str(context.exception)
        )

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.cinst.factory")
    def test_load_cinst_kernel_success(self, mock_factory, mock_create):
        """Test successful loading of CInstructions from an iterator."""
        # Configure mocks
        mock_factory.return_value = "cinst_factory"
        mock_create.side_effect = self.mock_cinst

        # Call the function
        result = load_cinst_kernel(self.cinst_lines)

        # Verify the results
        self.assertEqual(result, self.mock_cinst)
        # Factory is called once per line, so 2 times total
        self.assertEqual(mock_factory.call_count, 2)
        self.assertEqual(mock_create.call_count, 2)
        mock_create.assert_has_calls(
            [
                call(self.cinst_lines[0], "cinst_factory"),
                call(self.cinst_lines[1], "cinst_factory"),
            ]
        )

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.cinst.factory")
    def test_load_cinst_kernel_failure(self, mock_factory, mock_create):
        """Test error handling when loading CInstructions fails."""
        # Configure mocks
        mock_factory.return_value = "cinst_factory"
        mock_create.return_value = None

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_cinst_kernel(self.cinst_lines)

        self.assertIn(
            f"Error parsing line 1: {self.cinst_lines[0]}", str(context.exception)
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_cinst_kernel")
    def test_load_cinst_kernel_from_file_success(self, mock_load, mock_file):
        """Test successful loading of CInstructions from a file."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.cinst_lines
        mock_load.return_value = self.mock_cinst

        # Call the function
        result = load_cinst_kernel_from_file("test.cinst")

        # Verify the results
        self.assertEqual(result, self.mock_cinst)
        mock_file.assert_called_once_with("test.cinst", "r")
        mock_load.assert_called_once_with(self.cinst_lines)

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_cinst_kernel")
    def test_load_cinst_kernel_from_file_failure(self, mock_load, mock_file):
        """Test error handling when loading CInstructions from a file fails."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.cinst_lines
        mock_load.side_effect = Exception("Test error")

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_cinst_kernel_from_file("test.cinst")

        self.assertIn(
            'Error occurred loading file "test.cinst"', str(context.exception)
        )

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.xinst.factory")
    def test_load_xinst_kernel_success(self, mock_factory, mock_create):
        """Test successful loading of XInstructions from an iterator."""
        # Configure mocks
        mock_factory.return_value = "xinst_factory"
        mock_create.side_effect = self.mock_xinst

        # Call the function
        result = load_xinst_kernel(self.xinst_lines)

        # Verify the results
        self.assertEqual(result, self.mock_xinst)
        # Factory is called once per line, so 2 times total
        self.assertEqual(mock_factory.call_count, 2)
        self.assertEqual(mock_create.call_count, 2)
        mock_create.assert_has_calls(
            [
                call(self.xinst_lines[0], "xinst_factory"),
                call(self.xinst_lines[1], "xinst_factory"),
            ]
        )

    @patch("linker.instructions.create_from_str_line")
    @patch("linker.instructions.xinst.factory")
    def test_load_xinst_kernel_failure(self, mock_factory, mock_create):
        """Test error handling when loading XInstructions fails."""
        # Configure mocks
        mock_factory.return_value = "xinst_factory"
        mock_create.return_value = None

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_xinst_kernel(self.xinst_lines)

        self.assertIn(
            f"Error parsing line 1: {self.xinst_lines[0]}", str(context.exception)
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_xinst_kernel")
    def test_load_xinst_kernel_from_file_success(self, mock_load, mock_file):
        """Test successful loading of XInstructions from a file."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.xinst_lines
        mock_load.return_value = self.mock_xinst

        # Call the function
        result = load_xinst_kernel_from_file("test.xinst")

        # Verify the results
        self.assertEqual(result, self.mock_xinst)
        mock_file.assert_called_once_with("test.xinst", "r")
        mock_load.assert_called_once_with(self.xinst_lines)

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_xinst_kernel")
    def test_load_xinst_kernel_from_file_failure(self, mock_load, mock_file):
        """Test error handling when loading XInstructions from a file fails."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.xinst_lines
        mock_load.side_effect = Exception("Test error")

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_xinst_kernel_from_file("test.xinst")

        self.assertIn(
            'Error occurred loading file "test.xinst"', str(context.exception)
        )

    @patch("linker.instructions.dinst.create_from_mem_line")
    def test_load_dinst_kernel_success(self, mock_create):
        """Test successful loading of DInstructions from an iterator."""
        # Configure mocks
        mock_create.side_effect = self.mock_dinst

        # Call the function
        result = load_dinst_kernel(self.dinst_lines)

        # Verify the results
        self.assertEqual(result, self.mock_dinst)
        self.assertEqual(mock_create.call_count, 2)
        mock_create.assert_has_calls(
            [call(self.dinst_lines[0]), call(self.dinst_lines[1])]
        )

    @patch("linker.instructions.dinst.create_from_mem_line")
    def test_load_dinst_kernel_failure(self, mock_create):
        """Test error handling when loading DInstructions fails."""
        # Configure mocks
        mock_create.return_value = None

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_dinst_kernel(self.dinst_lines)

        self.assertIn(
            f"Error parsing line 1: {self.dinst_lines[0]}", str(context.exception)
        )

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_dinst_kernel")
    def test_load_dinst_kernel_from_file_success(self, mock_load, mock_file):
        """Test successful loading of DInstructions from a file."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.dinst_lines
        mock_load.return_value = self.mock_dinst

        # Call the function
        result = load_dinst_kernel_from_file("test.dinst")

        # Verify the results
        self.assertEqual(result, self.mock_dinst)
        mock_file.assert_called_once_with("test.dinst", "r")
        mock_load.assert_called_once_with(self.dinst_lines)

    @patch("builtins.open", new_callable=mock_open)
    @patch("linker.loader.load_dinst_kernel")
    def test_load_dinst_kernel_from_file_failure(self, mock_load, mock_file):
        """Test error handling when loading DInstructions from a file fails."""
        # Configure mocks
        mock_file.return_value.__enter__.return_value = self.dinst_lines
        mock_load.side_effect = Exception("Test error")

        # Call the function and check for exception
        with self.assertRaises(RuntimeError) as context:
            load_dinst_kernel_from_file("test.dinst")

        self.assertIn(
            'Error occurred loading file "test.dinst"', str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
