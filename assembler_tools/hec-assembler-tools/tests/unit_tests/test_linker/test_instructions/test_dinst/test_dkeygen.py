# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Unit tests for the DKeygen instruction class.

This module tests the functionality of the DKeygen instruction which is
responsible for key generation operations.
"""

import unittest
from unittest.mock import patch

from assembler.memory_model.mem_info import MemInfo
from linker.instructions.dinst.dkeygen import Instruction


class TestDKeygenInstruction(unittest.TestCase):
    """
    @brief Test cases for the DKeygen instruction class.

    @details These tests verify that the DKeygen instruction correctly handles token
    parsing, name resolution, and serialization.
    """

    def setUp(self):
        # Create the instruction with sample parameters
        self.seed_idx = 1
        self.key_idx = 2
        self.var_name = "var1"
        self.inst = Instruction(
            [Instruction.name, self.seed_idx, self.key_idx, self.var_name]
        )

    def test_get_num_tokens(self):
        """@brief Test that _get_num_tokens returns 4

        @test Verifies the instruction requires exactly 4 tokens
        """
        self.assertEqual(Instruction.num_tokens, 4)

    def test_get_name(self):
        """@brief Test that _get_name returns the expected value

        @test Verifies the instruction name matches the MemInfo constant
        """
        self.assertEqual(Instruction.name, MemInfo.Const.Keyword.KEYGEN)

    def test_initialization_valid_input(self):
        """@brief Test that initialization can set up the correct properties with valid name

        @test Verifies the instruction is properly initialized with valid tokens
        """
        inst = Instruction(
            [MemInfo.Const.Keyword.KEYGEN, self.seed_idx, self.key_idx, self.var_name]
        )
        self.assertEqual(inst.name, MemInfo.Const.Keyword.KEYGEN)

    def test_initialization_invalid_name(self):
        """@brief Test that initialization raises exception with invalid name

        @test Verifies ValueError is raised when an invalid instruction name is provided
        """
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction(["invalid_name", self.seed_idx, self.key_idx, self.var_name])

    def test_tokens_property(self):
        """@brief Test that tokens property returns the correct list

        @test Verifies the tokens property correctly formats the instruction tokens
        """
        # Since tokens property implementation is not visible in the dkeygen.py file,
        # this test assumes default behavior from parent class or basic functionality
        expected_tokens = [
            MemInfo.Const.Keyword.KEYGEN,
            self.seed_idx,
            self.key_idx,
            self.var_name,
        ]
        self.assertEqual(self.inst.tokens[:4], expected_tokens)

    def test_tokens_with_additional_data(self):
        """@brief Test tokens property with additional tokens

        @test Verifies extra tokens are preserved in the tokens property
        """
        additional_token = "extra"
        inst_with_extra = Instruction(
            [
                Instruction.name,
                self.seed_idx,
                self.key_idx,
                self.var_name,
                additional_token,
            ]
        )
        # If tokens property uses default implementation, it should include the additional token
        self.assertIn(additional_token, inst_with_extra.tokens)

    @patch(
        "linker.instructions.dinst.dinstruction.DInstruction.__init__",
        return_value=None,
    )
    def test_inheritance(self, mock_init):
        """@brief Test that Instruction properly extends DInstruction

        @test Verifies the parent constructor is called during initialization
        """
        # Ensure that DInstruction methods are called as expected
        Instruction([Instruction.name, self.seed_idx, self.key_idx, self.var_name])
        # Verify DInstruction.__init__ was called
        mock_init.assert_called()

    def test_invalid_token_count_too_few(self):
        """@brief Test behavior when fewer tokens than required are provided

        @test Verifies ValueError is raised when too few tokens are provided
        """
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction([MemInfo.Const.Keyword.KEYGEN, self.seed_idx, self.key_idx])

    def test_invalid_token_count_too_many(self):
        """@brief Test behavior when more tokens than required are provided

        @test Verifies extra tokens are handled gracefully without errors
        """
        # This should not raise an error as additional tokens are handled
        inst = Instruction(
            [
                MemInfo.Const.Keyword.KEYGEN,
                self.seed_idx,
                self.key_idx,
                self.var_name,
                "extra1",
                "extra2",
            ]
        )
        # Check that basic properties are still set correctly
        self.assertEqual(inst.name, MemInfo.Const.Keyword.KEYGEN)


if __name__ == "__main__":
    unittest.main()
