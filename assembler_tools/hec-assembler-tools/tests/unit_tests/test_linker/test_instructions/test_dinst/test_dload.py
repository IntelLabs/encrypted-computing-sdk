# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for the DLoad instruction class.

This module tests the functionality of the DLoad instruction which is
responsible for loading data from memory locations.
"""

import unittest
from unittest.mock import patch

from assembler.memory_model.mem_info import MemInfo
from linker.instructions.dinst.dload import Instruction


class TestDLoadInstruction(unittest.TestCase):
    """
    Test cases for the DLoad instruction class.

    These tests verify that the DLoad instruction correctly handles token
    parsing, name resolution, and serialization.
    """

    def setUp(self):
        # Create the instruction
        self.var_name = "test_var"
        self.address = 123
        self.type = "type1"

    def test_get_num_tokens(self):
        """Test that _get_num_tokens returns 3"""
        self.assertEqual(Instruction.num_tokens, 3)

    def test_get_name(self):
        """Test that _get_name returns the expected value"""
        self.assertEqual(Instruction.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_valid_input(self):
        """Test that initialization can set up the correct properties with valid name"""
        inst = Instruction(
            [MemInfo.Const.Keyword.LOAD, self.type, str(self.address), self.var_name]
        )

        self.assertEqual(inst.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_valid_meta(self):
        """Test that initialization can set up the correct properties with valid name"""
        inst = Instruction([MemInfo.Const.Keyword.LOAD, self.type, str(self.address)])

        self.assertEqual(inst.name, MemInfo.Const.Keyword.LOAD)

    def test_initialization_invalid_name(self):
        """Test that initialization raises exception with invalid name"""
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction(["invalid_name", self.type, str(self.address), self.var_name])

    def test_tokens_property(self):
        """Test that tokens property returns the correct list"""
        expected_tokens = [
            MemInfo.Const.Keyword.LOAD,
            self.type,
            str(self.address),
            self.var_name,
        ]
        inst = Instruction(
            [Instruction.name, self.type, str(self.address), self.var_name]
        )

        # Manually set properties to match expected behavior
        inst.address = self.address
        self.assertEqual(inst.tokens, expected_tokens)

    def test_tokens_with_additional_data(self):
        """Test tokens property with additional tokens"""
        additional_token = "extra"
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
        "linker.instructions.dinst.dinstruction.DInstruction.__init__",
        return_value=None,
    )
    def test_inheritance(self, mock_init):
        """Test that Instruction properly extends DInstruction"""
        # Ensure that DInstruction methods are called as expected
        Instruction([Instruction.name, self.type, str(self.address), self.var_name])
        # Verify DInstruction.__init__ was called
        mock_init.assert_called()

    def test_invalid_token_count_too_few(self):
        """Test behavior when fewer tokens than required are provided"""
        with self.assertRaises(ValueError):  # Adjust exception type if needed
            Instruction([MemInfo.Const.Keyword.LOAD, self.var_name])

    def test_invalid_token_count_too_many(self):
        """Test behavior when more tokens than required are provided"""
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
