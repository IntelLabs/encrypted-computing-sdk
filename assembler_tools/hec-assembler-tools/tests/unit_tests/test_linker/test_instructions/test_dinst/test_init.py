# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Unit tests for the dinst package initialization module.

This module tests the factory functions and initialization utilities for
data instructions.
"""

import unittest
from unittest.mock import patch, MagicMock

from linker.instructions.dinst import factory, create_from_mem_line
from linker.instructions.dinst import DLoad, DStore, DKeyGen


class TestDInstModule(unittest.TestCase):
    """
    @brief Test cases for data instruction initialization.

    @details These tests verify that the data instruction factory correctly creates
    instruction instances and properly handles initialization errors.
    """

    def test_factory(self):
        """@brief Test that factory returns the expected set of instruction classes

        @test Verifies the factory returns a set containing DLoad, DStore, and DKeyGen
        """
        instruction_set = factory()
        self.assertIsInstance(instruction_set, set)
        self.assertEqual(len(instruction_set), 3)
        self.assertIn(DLoad, instruction_set)
        self.assertIn(DStore, instruction_set)
        self.assertIn(DKeyGen, instruction_set)

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_dload_input(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line creates DLoad instruction

        @test Verifies that a DLoad instruction is created with correct properties
        """
        # Setup mocks
        tokens = ["dload", "poly", "0x123", "var1"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Setup MemInfo mock
        miv_mock = MagicMock()
        miv_mock.as_dict.return_value = {"var_name": "var1", "hbm_address": 0x123}
        mock_get_meminfo.return_value = (miv_mock, None)

        # Call function under test
        result = create_from_mem_line("dload, poly, 0x123, var1 # Test comment")

        # Verify results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DLoad)
        self.assertEqual(result.var, "var1")
        self.assertEqual(result.address, 0x123)

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_dload_meta(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line creates DLoad instruction for metadata

        @test Verifies that a DLoad instruction is created for metadata entries
        """
        # Setup mocks
        tokens = ["dload", "meta", "1"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Setup MemInfo mock
        miv_mock = MagicMock()
        miv_mock.as_dict.return_value = {"var_name": "meta1", "hbm_address": 1}
        mock_get_meminfo.return_value = (miv_mock, None)

        # Call function under test
        result = create_from_mem_line("dload, meta, 1 # Test comment")

        # Verify results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DLoad)
        self.assertEqual(result.var, "meta1")
        self.assertEqual(result.address, 1)

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_dstore(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line creates DStore instruction

        @test Verifies that a DStore instruction is created with correct properties
        """
        # Setup mocks
        tokens = ["dstore", "var1", "0x456"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Setup MemInfo mock
        miv_mock = MagicMock()
        miv_mock.as_dict.return_value = {"var_name": "var1", "hbm_address": 0x456}
        mock_get_meminfo.return_value = (miv_mock, None)

        # Call function under test
        result = create_from_mem_line("dstore, var1, 0x456 # Test comment")

        # Verify results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DStore)
        self.assertEqual(result.var, "var1")
        self.assertEqual(result.address, 0x456)

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_dkeygen(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line creates DKeyGen instruction

        @test Verifies that a DKeyGen instruction is created with correct properties
        """
        # Setup mocks
        tokens = ["keygen", "key1", "type1", "256"]
        comment = "Test comment"
        mock_tokenize.return_value = (tokens, comment)

        # Setup MemInfo mock
        miv_mock = MagicMock()
        miv_mock.as_dict.return_value = {"var_name": "key1", "hbm_address": 0x0}
        mock_get_meminfo.return_value = (miv_mock, None)

        # Call function under test
        result = create_from_mem_line("keygen, key1, type1, 256 # Test comment")

        # Verify results
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DKeyGen)
        # Verify var and address were set correctly
        self.assertEqual(result.var, "key1")
        self.assertEqual(result.address, 0x0)

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_invalid(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line with invalid instruction

        @test Verifies that RuntimeError is raised for invalid instructions
        """
        # Setup mocks to return invalid tokens
        tokens = ["invalid_instruction", "var1", "0x123"]
        comment = ""
        mock_tokenize.return_value = (tokens, comment)

        # Make get_meminfo_var_from_tokens raise RuntimeError
        mock_get_meminfo.side_effect = RuntimeError("Invalid instruction")

        # This should raise RuntimeError due to no valid instruction found
        with self.assertRaises(RuntimeError):
            create_from_mem_line("invalid_instruction, var1, 0x123")

    @patch("assembler.instructions.tokenize_from_line")
    @patch("assembler.memory_model.mem_info.MemInfo.get_meminfo_var_from_tokens")
    def test_create_from_mem_line_meminfo_error(self, mock_get_meminfo, mock_tokenize):
        """@brief Test create_from_mem_line with MemInfo error

        @test Verifies that RuntimeError is wrapped with line information
        """
        # Setup mocks
        tokens = ["dstore", "var1", "0x123"]
        comment = ""
        mock_tokenize.return_value = (tokens, comment)

        # Make get_meminfo_var_from_tokens raise RuntimeError
        mock_get_meminfo.side_effect = RuntimeError("Test error")

        # This should wrap the RuntimeError with information about the line
        with self.assertRaises(RuntimeError) as context:
            create_from_mem_line("dstore, var1, 0x123")

        # Verify the error message contains the original line
        self.assertIn("dstore, var1, 0x123", str(context.exception))


if __name__ == "__main__":
    unittest.main()
