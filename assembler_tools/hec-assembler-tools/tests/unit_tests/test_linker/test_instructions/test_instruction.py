# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for the BaseInstruction class.
"""

import os
import unittest
import tempfile
from unittest.mock import patch

from assembler.common.config import GlobalConfig
from linker.instructions.instruction import BaseInstruction


class MockInstruction(BaseInstruction):
    """@brief Concrete implementation of BaseInstruction for testing."""

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
    """@brief Tests for the BaseInstruction class."""

    def setUp(self):
        """@brief Setup for tests."""
        self.valid_tokens = ["TEST", "arg1", "arg2"]
        self.comment = "This is a test comment"

    def test_init_valid(self):
        """@brief Test initialization with valid tokens.

        @test Verifies that an instruction can be correctly initialized with valid tokens
        """
        instruction = MockInstruction(self.valid_tokens, self.comment)
        self.assertEqual(instruction.tokens, self.valid_tokens)
        self.assertEqual(instruction.comment, self.comment)

    def test_init_invalid_name(self):
        """@brief Test initialization with invalid instruction name.

        @test Verifies that a ValueError is raised when the instruction name is invalid
        """
        invalid_tokens = ["WRONG", "arg1", "arg2"]
        with self.assertRaises(ValueError) as context:
            MockInstruction(invalid_tokens)
        self.assertIn("invalid name", str(context.exception))

    def test_init_invalid_num_tokens(self):
        """@brief Test initialization with incorrect number of tokens.

        @test Verifies that a ValueError is raised when the number of tokens is incorrect
        """
        invalid_tokens = ["TEST", "arg1"]
        with self.assertRaises(ValueError) as context:
            MockInstruction(invalid_tokens)
        self.assertIn("invalid amount of tokens", str(context.exception))

    def test_id_generation(self):
        """@brief Test that each instruction gets a unique ID.

        @test Verifies that different instruction instances have different IDs
        """
        instruction1 = MockInstruction(self.valid_tokens)
        instruction2 = MockInstruction(self.valid_tokens)
        self.assertNotEqual(instruction1.id, instruction2.id)

    def test_str_representation(self):
        """@brief Test string representation.

        @test Verifies that the string representation is correctly formatted
        """
        instruction = MockInstruction(self.valid_tokens)
        self.assertEqual(str(instruction), f"TEST({instruction.id})")

    def test_repr_representation(self):
        """@brief Test repr representation.

        @test Verifies that the repr representation contains the expected information
        """
        instruction = MockInstruction(self.valid_tokens)
        self.assertIn("MockInstruction(TEST, id=", repr(instruction))
        self.assertIn("tokens=", repr(instruction))

    def test_equality(self):
        """@brief Test equality operator.

        @test Verifies that equality is based on object identity rather than value
        """
        instruction1 = MockInstruction(self.valid_tokens)
        instruction2 = MockInstruction(self.valid_tokens)
        self.assertNotEqual(instruction1, instruction2)
        self.assertEqual(instruction1, instruction1)

    def test_hash(self):
        """@brief Test hash function.

        @test Verifies that the hash is based on the instruction's ID
        """
        instruction = MockInstruction(self.valid_tokens)
        self.assertEqual(hash(instruction), hash(instruction.id))

    def test_to_line_with_comment(self):
        """@brief Test to_line method with comment.

        @test Verifies that to_line correctly includes the comment when present
        """
        instruction = MockInstruction(self.valid_tokens, self.comment)
        expected = f"TEST, arg1, arg2 # {self.comment}"
        self.assertEqual(instruction.to_line(), expected)

    def test_to_line_without_comment(self):
        """@brief Test to_line method without comment.

        @test Verifies that to_line works correctly when no comment is present
        """
        instruction = MockInstruction(self.valid_tokens)
        expected = "TEST, arg1, arg2"
        self.assertEqual(instruction.to_line(), expected)

    def test_to_line_suppressed_comments(self):
        """@brief Test to_line method with suppressed comments.

        @test Verifies that comments are not included when GlobalConfig.suppress_comments is True
        """
        with patch.object(GlobalConfig, "suppress_comments", True):
            instruction = MockInstruction(self.valid_tokens, self.comment)
            expected = "TEST, arg1, arg2"
            self.assertEqual(instruction.to_line(), expected)

    def test_dump_instructions_to_file(self):
        """@brief Test dump_instructions_to_file method.

        @test Verifies that instructions are correctly written to a file
        """
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
