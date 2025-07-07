# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the linker instructions initialization module.

This module contains tests that verify the behavior of the instruction factory
and initialization functionality.
"""

import unittest
from unittest.mock import patch, MagicMock

from linker.instructions import create_from_str_line


class TestCreateFromStrLine(unittest.TestCase):
    """
    @brief Test cases for instruction initialization functionality.

    These tests verify that instructions are correctly initialized,
    their tokens are properly processed, and their factories work as expected.
    """

    def setUp(self):
        # Create a mock class (not instance)
        self.mock_class = MagicMock()

        # Create a mock instance that will be returned when the class is called
        self.mock_instance = MagicMock()
        self.mock_instance.__bool__.return_value = True

        # Configure the class to return the instance when called
        self.mock_class.return_value = self.mock_instance

        # Create a factory with the mock class
        self.factory = {self.mock_class}

    @patch("linker.instructions.tokenize_from_line")
    def test_create_from_str_line_success(self, mock_tokenize):
        """
        @brief Test successful instruction creation

        @test Verifies that an instruction is correctly created from a string line
        when a valid factory is provided
        """
        # Setup mock
        tokens = ["instruction", "arg1", "arg2"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Call function
        result = create_from_str_line(
            "instruction, arg1, arg2 # Test comment", self.factory
        )

        # Verify
        mock_tokenize.assert_called_once_with("instruction, arg1, arg2 # Test comment")
        self.mock_class.assert_called_once_with(tokens, comment)
        self.assertEqual(result, self.mock_instance)

    @patch("linker.instructions.tokenize_from_line")
    def test_create_from_str_line_failure(self, mock_tokenize):
        """
        @brief Test when no instruction can be created

        @test Verifies that None is returned when instruction creation fails
        """
        # Setup mock
        tokens = ["unknown", "arg1", "arg2"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Make instruction creation fail
        self.mock_class.side_effect = ValueError("Invalid instruction")

        # Call function
        result = create_from_str_line(
            "unknown, arg1, arg2 # Test comment", self.factory
        )

        # Verify
        self.assertIsNone(result)

    @patch("linker.instructions.tokenize_from_line")
    def test_create_from_str_line_multiple_instruction_types(self, mock_tokenize):
        """
        @brief Test with multiple instruction types in factory

        @test Verifies that the function tries each instruction type in the factory
        until one succeeds
        """
        # Setup mocks
        tokens = ["instruction", "arg1", "arg2"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Create a second mock instruction class that fails
        mock_class2 = MagicMock()
        mock_class2.side_effect = ValueError("Invalid instruction")

        # Set up the factory with a specific order - use a list instead of a set
        # to control the iteration order
        factory = [mock_class2, self.mock_class]

        # Call function
        result = create_from_str_line("instruction, arg1, arg2 # Test comment", factory)

        # Verify that it tried both instruction types and returned the successful one
        mock_class2.assert_called_once_with(tokens, comment)
        self.mock_class.assert_called_once_with(tokens, comment)
        mock_class2.assert_called_once()
        self.assertEqual(result, self.mock_instance)

    @patch("linker.instructions.tokenize_from_line")
    def test_create_from_str_line_exception_handling(self, mock_tokenize):
        """
        @brief Test that general exceptions are caught

        @test Verifies that unexpected exceptions during instruction creation are
        handled gracefully and None is returned
        """
        # Setup mock
        tokens = ["instruction", "arg1", "arg2"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Make instruction creation raise a different exception
        self.mock_class.side_effect = Exception("Unexpected error")

        # Call function - should handle the exception and return None
        result = create_from_str_line(
            "instruction, arg1, arg2 # Test comment", self.factory
        )

        # Verify
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
