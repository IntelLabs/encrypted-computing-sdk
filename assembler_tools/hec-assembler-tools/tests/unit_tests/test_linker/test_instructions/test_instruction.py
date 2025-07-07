# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the BaseInstruction class.
"""

import os
import unittest
import tempfile
from unittest.mock import patch

from assembler.common.config import GlobalConfig
from linker.instructions.instruction import BaseInstruction


class MockInstruction(BaseInstruction):
    """Concrete implementation of BaseInstruction for testing."""

    @classmethod
    def _get_name(cls) -> str:
        return "TEST"

    @classmethod
    def _get_name_token_index(cls) -> int:
        return 0

    @classmethod
    def _get_num_tokens(cls) -> int:
        return 3


class TestBaseInstruction(unittest.TestCase):
    """Tests for the BaseInstruction class."""

    def setUp(self):
        """Setup for tests."""
        self.valid_tokens = ["TEST", "arg1", "arg2"]
        self.comment = "This is a test comment"

    def test_init_valid(self):
        """Test initialization with valid tokens."""
        instruction = MockInstruction(self.valid_tokens, self.comment)
        self.assertEqual(instruction.tokens, self.valid_tokens)
        self.assertEqual(instruction.comment, self.comment)

    def test_init_invalid_name(self):
        """Test initialization with invalid instruction name."""
        invalid_tokens = ["WRONG", "arg1", "arg2"]
        with self.assertRaises(ValueError) as context:
            MockInstruction(invalid_tokens)
        self.assertIn("invalid name", str(context.exception))

    def test_init_invalid_num_tokens(self):
        """Test initialization with incorrect number of tokens."""
        invalid_tokens = ["TEST", "arg1"]
        with self.assertRaises(ValueError) as context:
            MockInstruction(invalid_tokens)
        self.assertIn("invalid amount of tokens", str(context.exception))

    def test_id_generation(self):
        """Test that each instruction gets a unique ID."""
        instruction1 = MockInstruction(self.valid_tokens)
        instruction2 = MockInstruction(self.valid_tokens)
        self.assertNotEqual(instruction1.id, instruction2.id)

    def test_str_representation(self):
        """Test string representation."""
        instruction = MockInstruction(self.valid_tokens)
        self.assertEqual(str(instruction), f"TEST({instruction.id})")

    def test_repr_representation(self):
        """Test repr representation."""
        instruction = MockInstruction(self.valid_tokens)
        self.assertIn("MockInstruction(TEST, id=", repr(instruction))
        self.assertIn("tokens=", repr(instruction))

    def test_equality(self):
        """Test equality operator."""
        instruction1 = MockInstruction(self.valid_tokens)
        instruction2 = MockInstruction(self.valid_tokens)
        self.assertNotEqual(instruction1, instruction2)
        self.assertEqual(instruction1, instruction1)

    def test_hash(self):
        """Test hash function."""
        instruction = MockInstruction(self.valid_tokens)
        self.assertEqual(hash(instruction), hash(instruction.id))

    def test_to_line_with_comment(self):
        """Test to_line method with comment."""
        instruction = MockInstruction(self.valid_tokens, self.comment)
        expected = f"TEST, arg1, arg2 # {self.comment}"
        self.assertEqual(instruction.to_line(), expected)

    def test_to_line_without_comment(self):
        """Test to_line method without comment."""
        instruction = MockInstruction(self.valid_tokens)
        expected = "TEST, arg1, arg2"
        self.assertEqual(instruction.to_line(), expected)

    def test_to_line_suppressed_comments(self):
        """Test to_line method with suppressed comments."""
        with patch.object(GlobalConfig, "suppress_comments", True):
            instruction = MockInstruction(self.valid_tokens, self.comment)
            expected = "TEST, arg1, arg2"
            self.assertEqual(instruction.to_line(), expected)

    def test_dump_instructions_to_file(self):
        """Test dump_instructions_to_file method."""
        instruction1 = MockInstruction(self.valid_tokens, "Comment 1")
        instruction2 = MockInstruction(self.valid_tokens, "Comment 2")
        instructions = [instruction1, instruction2]

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name

        try:
            BaseInstruction.dump_instructions_to_file(instructions, file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()

            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0], instruction1.to_line())
            self.assertEqual(lines[1], instruction2.to_line())
        finally:
            os.unlink(file_path)


if __name__ == "__main__":
    unittest.main()
