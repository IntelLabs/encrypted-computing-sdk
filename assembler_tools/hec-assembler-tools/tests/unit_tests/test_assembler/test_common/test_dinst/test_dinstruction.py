# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Unit tests for the DInstruction base class.

This module tests the core functionality of the DInstruction class which
serves as the base for all data instructions.
"""

import unittest
from unittest.mock import MagicMock, patch

from assembler.common.dinst.dinstruction import DInstruction


class TestDInstruction(unittest.TestCase):
    """
    @brief Test cases for the DInstruction base class.

    @details These tests verify the common functionality shared by all data instructions,
    including token handling, ID generation, and property access.
    """

    def setUp(self):
        # Create a mock MemInfoVar class for testing
        self.mock_miv = MagicMock()
        self.mock_miv.as_dict.return_value = {"var_name": "var1", "hbm_address": 123}

        # Patch the MemInfo.get_meminfo_var_from_tokens method
        self.mem_info_patcher = patch("assembler.common.dinst.dinstruction.MemInfo.get_meminfo_var_from_tokens")
        self.mock_get_meminfo = self.mem_info_patcher.start()
        self.mock_get_meminfo.return_value = (self.mock_miv, 1)

        # Create a concrete subclass for testing since DInstruction is abstract
        class ConcreteDInstruction(DInstruction):
            """
            @brief Concrete implementation of DInstruction for testing purposes.

            @details This class provides implementations of the abstract methods
            required to instantiate and test the DInstruction class.
            """

            @classmethod
            def _get_num_tokens(cls) -> int:
                return 3

            @classmethod
            def _get_name(cls) -> str:
                return "dload"

        self.d_instruction_class = ConcreteDInstruction
        self.tokens = ["dload", "var1", "123"]
        self.comment = "Test comment"
        self.dinst = self.d_instruction_class(self.tokens, self.comment)

    def tearDown(self):
        # Stop the patcher
        self.mem_info_patcher.stop()

    def test_get_name_token_index(self):
        """@brief Test _get_name_token_index returns 0

        @test Verifies the name token is at index 0
        """
        self.assertEqual(self.d_instruction_class.name_token_index, 0)  # Updated reference

    def test_num_tokens_property(self):
        """@brief Test num_tokens property returns expected value

        @test Verifies the num_tokens property returns the value from _get_num_tokens
        """
        self.assertEqual(self.d_instruction_class.num_tokens, 3)  # Updated reference

    def test_initialization_valid_tokens(self):
        """@brief Test initialization with valid tokens

        @test Verifies an instance can be created with valid tokens and properties are set correctly
        """
        inst = self.d_instruction_class(self.tokens, self.comment)
        self.assertEqual(inst.tokens, self.tokens)
        self.assertEqual(inst.comment, self.comment)
        self.assertIsNotNone(inst.id)

    def test_initialization_token_count_too_few(self):
        """@brief Test initialization with too few tokens

        @test Verifies ValueError is raised when too few tokens are provided
        """
        with self.assertRaises(ValueError):
            self.d_instruction_class(["test_instruction", "var1"])

    def test_initialization_invalid_name(self):
        """@brief Test initialization with invalid name token

        @test Verifies ValueError is raised when an invalid instruction name is provided
        """
        with self.assertRaises(ValueError):
            self.d_instruction_class(["wrong_name", "var1", "123"])

    def test_id_property(self):
        """@brief Test id property returns a unique id

        @test Verifies each instruction instance gets a unique ID
        """
        inst1 = self.d_instruction_class(self.tokens)
        inst2 = self.d_instruction_class(self.tokens)
        self.assertNotEqual(inst1.id, inst2.id)

    def test_consecutive_ids(self):
        """@brief Test that consecutive instructions get incremental ids

        @test Verifies IDs are incremented sequentially for new instances
        """
        inst1 = self.d_instruction_class(self.tokens)
        inst2 = self.d_instruction_class(self.tokens)
        self.assertEqual(inst2.id, inst1.id + 1)

    def test_var_and_address_properties(self):
        """@brief Test var and address properties are correctly set from MemInfo

        @test Verifies the var and address properties are set from MemInfo during initialization
        """
        # Check that var and address were set from the mock MemInfo data
        self.assertEqual(self.dinst.var, "var1")
        self.assertEqual(self.dinst.address, 123)

        # Test property setters
        self.dinst.var = "new_var"
        self.assertEqual(self.dinst.var, "new_var")

        self.dinst.address = 456
        self.assertEqual(self.dinst.address, 456)

    def test_memory_info_error_handling(self):
        """@brief Test error handling when MemInfo parsing fails

        @test Verifies that when MemInfo parsing fails, a ValueError is raised
        with information about the parsing failure
        """
        # Make the mock raise an exception
        error_message = "Test error"
        self.mock_get_meminfo.side_effect = RuntimeError(error_message)

        # The DInstruction.__init__ should convert RuntimeError to ValueError
        with self.assertRaises(ValueError) as context:
            self.d_instruction_class(self.tokens, self.comment)

        # Verify the error message contains the original error
        self.assertIn(error_message, str(context.exception))


if __name__ == "__main__":
    unittest.main()
