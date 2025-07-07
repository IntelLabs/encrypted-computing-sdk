# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the DInstruction base class.

This module tests the core functionality of the DInstruction class which
serves as the base for all data instructions.
"""

import unittest

from linker.instructions.dinst.dinstruction import DInstruction


class TestDInstruction(unittest.TestCase):
    """
    Test cases for the DInstruction base class.

    These tests verify the common functionality shared by all data instructions,
    including token handling, ID generation, and property access.
    """

    def setUp(self):
        # Create a concrete subclass for testing since DInstruction is abstract
        class ConcreteDInstruction(DInstruction):
            """
            Concrete implementation of DInstruction for testing purposes.

            This class provides implementations of the abstract methods
            required to instantiate and test the DInstruction class.
            """

            @classmethod
            def _get_num_tokens(cls) -> int:
                return 3

            @classmethod
            def _get_name(cls) -> str:
                return "test_instruction"

        self.d_instruction_class = ConcreteDInstruction  # Changed to snake_case
        self.tokens = ["test_instruction", "var1", "123"]
        self.comment = "Test comment"
        self.dinst = self.d_instruction_class(self.tokens, self.comment)

    def test_get_name_token_index(self):
        """Test _get_name_token_index returns 0"""
        self.assertEqual(
            self.d_instruction_class.name_token_index, 0
        )  # Updated reference

    def test_num_tokens_property(self):
        """Test num_tokens property returns expected value"""
        self.assertEqual(self.d_instruction_class.num_tokens, 3)  # Updated reference

    def test_initialization_valid_tokens(self):
        """Test initialization with valid tokens"""
        inst = self.d_instruction_class(self.tokens, self.comment)
        self.assertEqual(inst.tokens, self.tokens)
        self.assertEqual(inst.comment, self.comment)
        self.assertIsNotNone(inst.id)

    def test_initialization_token_count_too_few(self):
        """Test initialization with too few tokens"""
        with self.assertRaises(ValueError):
            self.d_instruction_class(["test_instruction", "var1"])

    def test_initialization_invalid_name(self):
        """Test initialization with invalid name token"""
        with self.assertRaises(ValueError):
            self.d_instruction_class(["wrong_name", "var1", "123"])

    def test_id_property(self):
        """Test id property returns a unique id"""
        inst1 = self.d_instruction_class(self.tokens)
        inst2 = self.d_instruction_class(self.tokens)
        self.assertNotEqual(inst1.id, inst2.id)

    def test_to_line_method(self):
        """Test to_line method returns expected string"""
        tokens = ["test_instruction", "var1", "123"]
        inst = self.d_instruction_class(tokens, "")
        expected = "test_instruction, var1, 123"
        self.assertEqual(inst.to_line(), expected)

    def test_consecutive_ids(self):
        """Test that consecutive instructions get incremental ids"""
        inst1 = self.d_instruction_class(self.tokens)
        inst2 = self.d_instruction_class(self.tokens)
        self.assertEqual(inst2.id, inst1.id + 1)


if __name__ == "__main__":
    unittest.main()
