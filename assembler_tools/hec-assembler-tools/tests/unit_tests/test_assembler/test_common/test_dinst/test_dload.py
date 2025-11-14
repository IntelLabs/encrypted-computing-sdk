# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Unit tests for the DLoad instruction class.

This module tests the functionality of the DLoad instruction which is
responsible for loading data from memory locations.
"""

import unittest
from unittest.mock import patch

from assembler.common.dinst.dload import Instruction
from assembler.memory_model.mem_info import MemInfo


class TestDLoadInstruction(unittest.TestCase):
    """
    @brief Test cases for the DLoad instruction class.

    @details These tests verify that the DLoad instruction correctly handles token
    parsing, name resolution, and serialization.
    """

    def setUp(self):
        # Create the instruction
        self.var_name = "test_var"
        self.address = 123
        self.type = "poly"

    def test_get_num_tokens(self):
        """@brief Test that _get_num_tokens returns 3

        @test Verifies the instruction requires exactly 3 tokens
        """
        self.assertEqual(Instruction.num_tokens, 3)

    def test_get_name(self):
        """@brief Test that _get_name returns the expected value

        @test Verifies the instruction name matches the MemInfo constant
        """
        self.assertEqual(Instruction.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_valid_input(self):
        """@brief Test that initialization can set up the correct properties with valid name

        @test Verifies the instruction is properly initialized with valid tokens
        """
        inst = Instruction([MemInfo.Const.Keyword.LOAD, self.type, str(self.address), self.var_name])

        self.assertEqual(inst.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_valid_meta(self):
        """@brief Test that initialization can set up the correct properties with metadata

        @test Verifies the instruction handles metadata loading correctly
        """
        metadata = "ones"
        inst = Instruction([MemInfo.Const.Keyword.LOAD, metadata, str(self.address)])

        self.assertEqual(inst.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_invalid_name(self):
        """@brief Test that initialization raises exception with invalid name

        @test Verifies ValueError is raised when an invalid instruction name is provided
        """
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction(["invalid_name", self.type, str(self.address), self.var_name])

    def test_tokens_property(self):
        """@brief Test that tokens property returns the correct list

        @test Verifies the tokens property correctly formats the instruction tokens
        """
        expected_tokens = [
            MemInfo.Const.Keyword.LOAD,
            self.type,
            str(self.address),
            self.var_name,
        ]
        inst = Instruction([Instruction.name, self.type, str(self.address), self.var_name])

        self.assertEqual(inst.tokens, expected_tokens)

    def test_tokens_with_additional_data(self):
        """@brief Test tokens property with additional tokens

        @test Verifies extra tokens are preserved in the tokens property
        """
        additional_token = "extra"  # noqa: S105 (allow hardcoded string)
        inst_with_extra = Instruction(
            [
                Instruction.name,
                self.type,
                str(self.address),
                self.var_name,
                additional_token,
            ]
        )
        inst_with_extra.address = self.address
        expected_tokens = [
            MemInfo.Const.Keyword.LOAD,
            self.type,
            str(self.address),
            self.var_name,
            additional_token,
        ]
        self.assertEqual(inst_with_extra.tokens, expected_tokens)

    @patch(
        "assembler.common.dinst.dinstruction.DInstruction.__init__",
        return_value=None,
    )
    def test_inheritance(self, mock_init):
        """@brief Test that Instruction properly extends DInstruction

        @test Verifies the parent constructor is called during initialization
        """
        # Ensure that DInstruction methods are called as expected
        Instruction([Instruction.name, self.type, str(self.address), self.var_name])
        # Verify DInstruction.__init__ was called
        mock_init.assert_called()

    def test_invalid_token_count_too_few(self):
        """@brief Test behavior when fewer tokens than required are provided

        @test Verifies ValueError is raised when too few tokens are provided
        """
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction([MemInfo.Const.Keyword.LOAD, self.var_name])

    def test_invalid_token_count_too_many(self):
        """@brief Test behavior when more tokens than required are provided

        @test Verifies extra tokens are handled gracefully without errors
        """
        # This should not raise an error as additional tokens are handled
        inst = Instruction(
            [
                MemInfo.Const.Keyword.LOAD,
                self.type,
                str(self.address),
                self.var_name,
                "extra1",
                "extra2",
            ]
        )

        # Check that basic properties are still set correctly
        self.assertEqual(inst.name, MemInfo.Const.Keyword.LOAD)


if __name__ == "__main__":
    unittest.main()
