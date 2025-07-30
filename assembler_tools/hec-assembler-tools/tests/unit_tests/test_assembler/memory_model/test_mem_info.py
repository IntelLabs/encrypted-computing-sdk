# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Unit tests for the memory model mem_info module.
"""

import unittest
from unittest.mock import MagicMock, PropertyMock, call, patch

from assembler.memory_model import MemoryModel
from assembler.memory_model.mem_info import (
    MemInfo,
    MemInfoKeygenVariable,
    MemInfoVariable,
    _allocateMemInfoVariable,
    updateMemoryModelWithMemInfo,
)


class TestMemInfoVariable(unittest.TestCase):
    """@brief Tests for the MemInfoVariable class."""

    def test_init_valid(self):
        """@brief Test initialization with valid parameters."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoVariable("test_var", 42)
            self.assertEqual(var.var_name, "test_var")
            self.assertEqual(var.hbm_address, 42)

    def test_init_strips_whitespace(self):
        """@brief Test that initialization strips whitespace from variable name."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoVariable("  test_var  ", 42)
            self.assertEqual(var.var_name, "test_var")

    def test_init_invalid_name(self):
        """@brief Test initialization with invalid variable name."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=False):
            with self.assertRaises(RuntimeError):
                MemInfoVariable("invalid!var", 42)

    def test_repr(self):
        """@brief Test the __repr__ method."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoVariable("test_var", 42)
            self.assertEqual(repr(var), repr({"var_name": "test_var", "hbm_address": 42}))

    def test_as_dict(self):
        """@brief Test the as_dict method."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoVariable("test_var", 42)
            self.assertEqual(var.as_dict(), {"var_name": "test_var", "hbm_address": 42})


class TestMemInfoKeygenVariable(unittest.TestCase):
    """@brief Tests for the MemInfoKeygenVariable class."""

    def test_init_valid(self):
        """@brief Test initialization with valid parameters."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoKeygenVariable("test_var", 2, 3)
            self.assertEqual(var.var_name, "test_var")
            self.assertEqual(var.hbm_address, -1)  # Should be initialized to -1
            self.assertEqual(var.seed_index, 2)
            self.assertEqual(var.key_index, 3)

    def test_init_negative_seed_index(self):
        """@brief Test initialization with negative seed index."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            with self.assertRaises(IndexError):
                MemInfoKeygenVariable("test_var", -1, 3)

    def test_init_negative_key_index(self):
        """@brief Test initialization with negative key index."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            with self.assertRaises(IndexError):
                MemInfoKeygenVariable("test_var", 2, -1)

    def test_as_dict(self):
        """@brief Test the as_dict method."""
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            var = MemInfoKeygenVariable("test_var", 2, 3)
            self.assertEqual(var.as_dict(), {"var_name": "test_var", "seed_index": 2, "key_index": 3})


class TestMemInfoMetadata(unittest.TestCase):
    """@brief Tests for the MemInfo.Metadata class."""

    def test_parse_meta_field_from_mem_tokens_valid(self):
        """@brief Test parsing a valid metadata field."""
        tokens = ["dload", "LOAD_ONES", "42", "ones_var"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES")
        self.assertIsNotNone(result)
        self.assertEqual(result.var_name, "ones_var")
        self.assertEqual(result.hbm_address, 42)

    def test_parse_meta_field_from_mem_tokens_no_name(self):
        """@brief Test parsing a metadata field without explicit name."""
        tokens = ["dload", "LOAD_ONES", "42"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES")
        self.assertIsNotNone(result)
        self.assertEqual(result.var_name, "ONES_42")
        self.assertEqual(result.hbm_address, 42)

    def test_parse_meta_field_from_mem_tokens_with_extra(self):
        """@brief Test parsing a metadata field with var_extra."""
        tokens = ["dload", "LOAD_ONES", "42"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES", var_extra="_extra")
        self.assertIsNotNone(result)
        self.assertEqual(result.var_name, "ONES_extra")
        self.assertEqual(result.hbm_address, 42)

    def test_parse_meta_field_from_mem_tokens_invalid(self):
        """@brief Test parsing an invalid metadata field."""
        # Not enough tokens
        tokens = ["dload"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES")
        self.assertIsNone(result)

        # Wrong first token
        tokens = ["wrong", "LOAD_ONES", "42"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES")
        self.assertIsNone(result)

        # Wrong second token
        tokens = ["dload", "WRONG", "42"]
        result = MemInfo.Metadata.parse_meta_field_from_mem_tokens(tokens, "LOAD_ONES", var_prefix="ONES")
        self.assertIsNone(result)

    def test_metadata_init_and_properties(self):
        """@brief Test initialization and properties of Metadata class."""
        # Prepare test data
        metadata_dict = {
            "ones": [{"var_name": "ones_var", "hbm_address": 1}],
            "ntt_auxiliary_table": [{"var_name": "ntt_aux", "hbm_address": 2}],
            "ntt_routing_table": [{"var_name": "ntt_route", "hbm_address": 3}],
            "intt_auxiliary_table": [{"var_name": "intt_aux", "hbm_address": 4}],
            "intt_routing_table": [{"var_name": "intt_route", "hbm_address": 5}],
            "twid": [{"var_name": "twiddle_var", "hbm_address": 6}],
            "keygen_seed": [{"var_name": "keygen_seed", "hbm_address": 7}],
        }

        # Initialize Metadata
        metadata = MemInfo.Metadata(**metadata_dict)

        # Test property access
        self.assertEqual(len(metadata.ones), 1)
        self.assertEqual(metadata.ones[0].var_name, "ones_var")

        self.assertEqual(len(metadata.ntt_auxiliary_table), 1)
        self.assertEqual(metadata.ntt_auxiliary_table[0].var_name, "ntt_aux")

        self.assertEqual(len(metadata.ntt_routing_table), 1)
        self.assertEqual(metadata.ntt_routing_table[0].var_name, "ntt_route")

        self.assertEqual(len(metadata.intt_auxiliary_table), 1)
        self.assertEqual(metadata.intt_auxiliary_table[0].var_name, "intt_aux")

        self.assertEqual(len(metadata.intt_routing_table), 1)
        self.assertEqual(metadata.intt_routing_table[0].var_name, "intt_route")

        self.assertEqual(len(metadata.twiddle), 1)
        self.assertEqual(metadata.twiddle[0].var_name, "twiddle_var")

        self.assertEqual(len(metadata.keygen_seeds), 1)
        self.assertEqual(metadata.keygen_seeds[0].var_name, "keygen_seed")

    def test_get_item(self):
        """@brief Test the __getitem__ method."""
        metadata_dict = {"ones": [{"var_name": "ones_var", "hbm_address": 1}]}
        metadata = MemInfo.Metadata(**metadata_dict)

        # Test __getitem__ using bracket notation
        ones_list = metadata["ones"]
        self.assertEqual(len(ones_list), 1)
        self.assertEqual(ones_list[0].var_name, "ones_var")


class TestMemInfoParsers(unittest.TestCase):
    """@brief Tests for the various parser methods in MemInfo."""

    def test_ones_parse_from_mem_tokens(self):
        """@brief Test parsing Ones metadata from tokens."""
        tokens = ["dload", "LOAD_ONES", "42", "ones_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.Ones.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_ONES,
                var_prefix=MemInfo.Const.Keyword.LOAD_ONES,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_ntt_aux_table_parse_from_mem_tokens(self):
        """@brief Test parsing NTTAuxTable metadata from tokens."""
        tokens = ["dload", "LOAD_NTT_AUX_TABLE", "42", "ntt_aux_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.NTTAuxTable.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_NTT_AUX_TABLE,
                var_prefix=MemInfo.Const.Keyword.LOAD_NTT_AUX_TABLE,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_ntt_routing_table_parse_from_mem_tokens(self):
        """@brief Test parsing NTTRoutingTable metadata from tokens."""
        tokens = ["dload", "LOAD_NTT_ROUTING_TABLE", "42", "ntt_route_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.NTTRoutingTable.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_NTT_ROUTING_TABLE,
                var_prefix=MemInfo.Const.Keyword.LOAD_NTT_ROUTING_TABLE,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_intt_aux_table_parse_from_mem_tokens(self):
        """@brief Test parsing iNTTAuxTable metadata from tokens."""
        tokens = ["dload", "LOAD_iNTT_AUX_TABLE", "42", "intt_aux_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.iNTTAuxTable.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_iNTT_AUX_TABLE,
                var_prefix=MemInfo.Const.Keyword.LOAD_iNTT_AUX_TABLE,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_intt_routing_table_parse_from_mem_tokens(self):
        """@brief Test parsing iNTTRoutingTable metadata from tokens."""
        tokens = ["dload", "LOAD_iNTT_ROUTING_TABLE", "42", "intt_route_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.iNTTRoutingTable.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_iNTT_ROUTING_TABLE,
                var_prefix=MemInfo.Const.Keyword.LOAD_iNTT_ROUTING_TABLE,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_twiddle_parse_from_mem_tokens(self):
        """@brief Test parsing Twiddle metadata from tokens."""
        tokens = ["dload", "LOAD_TWIDDLE", "42", "twiddle_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.Twiddle.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_TWIDDLE,
                var_prefix=MemInfo.Const.Keyword.LOAD_TWIDDLE,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_keygen_seed_parse_from_mem_tokens(self):
        """@brief Test parsing KeygenSeed metadata from tokens."""
        tokens = ["dload", "LOAD_KEYGEN_SEED", "42", "keygen_seed_var"]
        with patch("assembler.memory_model.mem_info.MemInfo.Metadata.parse_meta_field_from_mem_tokens") as mock_parse:
            mock_parse.return_value = MagicMock()
            result = MemInfo.Metadata.KeygenSeed.parse_from_mem_tokens(tokens)
            mock_parse.assert_called_once_with(
                tokens,
                MemInfo.Const.Keyword.LOAD_KEYGEN_SEED,
                var_prefix=MemInfo.Const.Keyword.LOAD_KEYGEN_SEED,
            )
            self.assertEqual(result, mock_parse.return_value)

    def test_keygen_parse_from_mem_tokens_valid(self):
        """@brief Test parsing a valid keygen variable."""
        tokens = ["keygen", "2", "3", "keygen_var"]
        result = MemInfo.Keygen.parse_from_mem_tokens(tokens)
        self.assertIsNotNone(result)
        self.assertEqual(result.var_name, "keygen_var")
        self.assertEqual(result.seed_index, 2)
        self.assertEqual(result.key_index, 3)

    def test_keygen_parse_from_mem_tokens_invalid(self):
        """@brief Test parsing an invalid keygen variable."""
        # Not enough tokens
        tokens = ["keygen", "2", "3"]
        result = MemInfo.Keygen.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

        # Wrong first token
        tokens = ["wrong", "2", "3", "keygen_var"]
        result = MemInfo.Keygen.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

    def test_input_parse_from_mem_tokens_valid(self):
        """@brief Test parsing a valid input variable."""
        tokens = ["dload", "poly", "42", "input_var"]
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            result = MemInfo.Input.parse_from_mem_tokens(tokens)
            self.assertIsNotNone(result)
            self.assertEqual(result.var_name, "input_var")
            self.assertEqual(result.hbm_address, 42)

    def test_input_parse_from_mem_tokens_invalid(self):
        """@brief Test parsing an invalid input variable."""
        # Not enough tokens
        tokens = ["dload", "poly", "42"]
        result = MemInfo.Input.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

        # Wrong tokens
        tokens = ["wrong", "poly", "42", "input_var"]
        result = MemInfo.Input.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

        tokens = ["dload", "wrong", "42", "input_var"]
        result = MemInfo.Input.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

    def test_output_parse_from_mem_tokens_valid(self):
        """@brief Test parsing a valid output variable."""
        tokens = ["dstore", "output_var", "42"]
        with patch("assembler.memory_model.variable.Variable.validateName", return_value=True):
            result = MemInfo.Output.parse_from_mem_tokens(tokens)
            self.assertIsNotNone(result)
            self.assertEqual(result.var_name, "output_var")
            self.assertEqual(result.hbm_address, 42)

    def test_output_parse_from_mem_tokens_invalid(self):
        """@brief Test parsing an invalid output variable."""
        # Not enough tokens
        tokens = ["store", "output_var"]
        result = MemInfo.Output.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)

        # Wrong first token
        tokens = ["wrong", "output_var", "42"]
        result = MemInfo.Output.parse_from_mem_tokens(tokens)
        self.assertIsNone(result)


class TestMemInfo(unittest.TestCase):
    """@brief Tests for the MemInfo class."""

    def test_init_default(self):
        """@brief Test default initialization."""
        mem_info = MemInfo()
        self.assertEqual(len(mem_info.keygens), 0)
        self.assertEqual(len(mem_info.inputs), 0)
        self.assertEqual(len(mem_info.outputs), 0)
        # Verify metadata was initialized
        self.assertIsInstance(mem_info.metadata, MemInfo.Metadata)

    def test_init_with_data(self):
        """@brief Test initialization with data."""
        # Prepare test data
        test_data = {
            "keygens": [{"var_name": "keygen_var", "seed_index": 1, "key_index": 2}],
            "inputs": [{"var_name": "input_var", "hbm_address": 42}],
            "outputs": [{"var_name": "output_var", "hbm_address": 43}],
            "metadata": {
                "ones": [{"var_name": "ones_var", "hbm_address": 44}],
                "twid": [{"var_name": "twiddle_var", "hbm_address": 45}],
            },
        }

        # Initialize with test data
        with patch("assembler.memory_model.mem_info.MemInfo.validate"):
            mem_info = MemInfo(**test_data)

            # Verify data was loaded correctly
            self.assertEqual(len(mem_info.keygens), 1)
            self.assertEqual(mem_info.keygens[0].var_name, "keygen_var")

            self.assertEqual(len(mem_info.inputs), 1)
            self.assertEqual(mem_info.inputs[0].var_name, "input_var")

            self.assertEqual(len(mem_info.outputs), 1)
            self.assertEqual(mem_info.outputs[0].var_name, "output_var")

            # Verify metadata
            self.assertEqual(len(mem_info.metadata.ones), 1)
            self.assertEqual(mem_info.metadata.ones[0].var_name, "ones_var")

            self.assertEqual(len(mem_info.metadata.twiddle), 1)
            self.assertEqual(mem_info.metadata.twiddle[0].var_name, "twiddle_var")

    def test_factory_dict(self):
        """@brief Test the factory_dict property."""
        mem_info = MemInfo()
        factory_dict = mem_info.factory_dict

        # Verify all expected keys are present
        self.assertIn(MemInfo.Keygen, factory_dict)
        self.assertIn(MemInfo.Input, factory_dict)
        self.assertIn(MemInfo.Output, factory_dict)
        self.assertIn(MemInfo.Metadata.KeygenSeed, factory_dict)
        self.assertIn(MemInfo.Metadata.Ones, factory_dict)
        self.assertIn(MemInfo.Metadata.NTTAuxTable, factory_dict)
        self.assertIn(MemInfo.Metadata.NTTRoutingTable, factory_dict)
        self.assertIn(MemInfo.Metadata.iNTTAuxTable, factory_dict)
        self.assertIn(MemInfo.Metadata.iNTTRoutingTable, factory_dict)
        self.assertIn(MemInfo.Metadata.Twiddle, factory_dict)

        # Verify values point to correct lists
        self.assertEqual(factory_dict[MemInfo.Keygen], mem_info.keygens)
        self.assertEqual(factory_dict[MemInfo.Input], mem_info.inputs)
        self.assertEqual(factory_dict[MemInfo.Output], mem_info.outputs)

    def test_mem_info_types(self):
        """@brief Test the mem_info_types class property."""
        mem_info_types = MemInfo.mem_info_types

        # Verify expected types are in the list
        self.assertIn(MemInfo.Keygen, mem_info_types)
        self.assertIn(MemInfo.Input, mem_info_types)
        self.assertIn(MemInfo.Output, mem_info_types)
        self.assertIn(MemInfo.Metadata.KeygenSeed, mem_info_types)
        self.assertIn(MemInfo.Metadata.Ones, mem_info_types)
        self.assertIn(MemInfo.Metadata.NTTAuxTable, mem_info_types)
        self.assertIn(MemInfo.Metadata.NTTRoutingTable, mem_info_types)
        self.assertIn(MemInfo.Metadata.iNTTAuxTable, mem_info_types)
        self.assertIn(MemInfo.Metadata.iNTTRoutingTable, mem_info_types)
        self.assertIn(MemInfo.Metadata.Twiddle, mem_info_types)

    def test_get_meminfo_var_from_tokens_valid(self):
        """@brief Test getting a MemInfo variable from valid tokens."""
        tokens = ["keygen", "2", "3", "keygen_var"]

        # Mock the parse_from_mem_tokens method to return a mock variable
        mock_variable = MagicMock()
        with patch.object(MemInfo.Keygen, "parse_from_mem_tokens", return_value=mock_variable):
            var, var_type = MemInfo.get_meminfo_var_from_tokens(tokens)

            # Verify results
            self.assertEqual(var, mock_variable)
            self.assertEqual(var_type, MemInfo.Keygen)

    def test_get_meminfo_var_from_tokens_not_found(self):
        """@brief Test getting a MemInfo variable when no parser can handle it."""
        tokens = ["unknown", "token"]

        # Mock all parse_from_mem_tokens methods to return None
        with patch.object(
            MemInfo,
            "mem_info_types",
            return_value=[MagicMock(parse_from_mem_tokens=MagicMock(return_value=None))],
        ):
            var, var_type = MemInfo.get_meminfo_var_from_tokens(tokens)

            # Verify results
            self.assertIsNone(var)
            self.assertIsNone(var_type)

    def test_add_meminfo_var_from_tokens_valid(self):
        """@brief Test adding a MemInfo variable from valid tokens."""
        tokens = ["keygen", "2", "3", "keygen_var"]
        mem_info = MemInfo()

        # Mock get_meminfo_var_from_tokens
        mock_variable = MagicMock()
        mock_type = MagicMock()
        mock_list = MagicMock()
        mock_dict = {mock_type: mock_list}

        with (
            patch.object(
                MemInfo,
                "get_meminfo_var_from_tokens",
                return_value=(mock_variable, mock_type),
            ),
            patch.object(MemInfo, "factory_dict", new_callable=PropertyMock, return_value=mock_dict),
        ):
            # Call the method
            mem_info.add_meminfo_var_from_tokens(tokens)

            # Verify the variable was added to the correct list
            mock_list.append.assert_called_once_with(mock_variable)

    def test_add_meminfo_var_from_tokens_not_found(self):
        """@brief Test adding a MemInfo variable when no parser can handle it."""
        tokens = ["unknown", "token"]
        mem_info = MemInfo()

        # Mock get_meminfo_var_from_tokens to return None
        with patch.object(MemInfo, "get_meminfo_var_from_tokens", return_value=(None, None)):
            # Verify exception is raised
            with self.assertRaises(RuntimeError):
                mem_info.add_meminfo_var_from_tokens(tokens)

    def test_from_file_iter_valid(self):
        """@brief Test creating a MemInfo from a valid file iterator."""
        # Mock lines
        lines = [
            "keygen, 2, 3, keygen_var",
            "dload, input, 42, input_var",
            "store, output_var, 43",
            "dload, LOAD_ONES, 44, ones_var",
            "  ",  # Empty line to test skipping
            "# Comment line",  # Comment line to test skipping
        ]

        # Mock tokenize_from_line
        def mock_tokenize(line):
            if line.startswith("keygen"):
                return (["keygen", "2", "3", "keygen_var"], "")
            if line.startswith("dload, input"):
                return (["dload", "input", "42", "input_var"], "")
            if line.startswith("store"):
                return (["store", "output_var", "43"], "")
            if line.startswith("dload, LOAD_ONES"):
                return (["dload", "LOAD_ONES", "44", "ones_var"], "")

            return ([], "")

        # Mock methods - patch the function where it's imported in mem_info
        with (
            patch(
                "assembler.memory_model.mem_info.tokenize_from_line",
                side_effect=mock_tokenize,
            ),
            patch.object(MemInfo, "add_meminfo_var_from_tokens") as mock_add_var,
            patch.object(MemInfo, "validate"),
        ):
            # Call the method
            MemInfo.from_file_iter(lines)

            # Verify add_meminfo_var_from_tokens was called for each valid line
            self.assertEqual(mock_add_var.call_count, 4)

    def test_from_file_iter_error(self):
        """@brief Test creating a MemInfo when an error occurs."""
        # Mock lines
        lines = ["invalid line"]

        # Mock tokenize_from_line
        def mock_tokenize(line):
            return (["invalid"], line)

        # Mock methods
        with (
            patch("assembler.instructions.tokenize_from_line", side_effect=mock_tokenize),
            patch.object(
                MemInfo,
                "add_meminfo_var_from_tokens",
                side_effect=RuntimeError("Test error"),
            ),
            patch.object(MemInfo, "validate"),
        ):
            # Verify exception is raised with line number and content
            with self.assertRaises(RuntimeError) as context:
                MemInfo.from_file_iter(lines)

            self.assertIn("1: invalid line", str(context.exception))

    def test_from_dinstrs_valid(self):
        """@brief Test creating a MemInfo from valid DInstructions."""
        # Mock DInstructions
        dinstrs = [
            MagicMock(tokens=["keygen", "2", "3", "keygen_var"]),
            MagicMock(tokens=["dload", "input", "42", "input_var"]),
            MagicMock(tokens=["store", "output_var", "43"]),
        ]

        # Mock methods
        with (
            patch.object(MemInfo, "add_meminfo_var_from_tokens") as mock_add_var,
            patch.object(MemInfo, "validate"),
            patch("builtins.print"),
        ):  # Mock print to avoid output
            # Call the method
            MemInfo.from_dinstrs(dinstrs)

            # Verify add_meminfo_var_from_tokens was called for each instruction
            self.assertEqual(mock_add_var.call_count, 3)
            mock_add_var.assert_has_calls(
                [
                    call(["keygen", "2", "3", "keygen_var"]),
                    call(["dload", "input", "42", "input_var"]),
                    call(["store", "output_var", "43"]),
                ]
            )

    def test_from_dinstrs_error(self):
        """@brief Test creating a MemInfo when an error occurs."""
        # Mock DInstructions
        dinstrs = [MagicMock(tokens=["invalid"])]

        # Mock methods
        with (
            patch.object(
                MemInfo,
                "add_meminfo_var_from_tokens",
                side_effect=RuntimeError("Test error"),
            ),
            patch.object(MemInfo, "validate"),
            patch("builtins.print"),
        ):  # Mock print to avoid output
            # Verify exception is raised with instruction number
            with self.assertRaises(RuntimeError) as context:
                MemInfo.from_dinstrs(dinstrs)

            self.assertIn("1: ['invalid']", str(context.exception))

    def test_as_dict(self):
        """@brief Test the as_dict method."""
        # Create a MemInfo with test data
        with patch("assembler.memory_model.mem_info.MemInfo.validate"):
            # dicts
            keygens_dict = {"var_name": "keygen_var", "seed_index": 1, "key_index": 2}
            inputs_dict = {"var_name": "input_var", "hbm_address": 42}
            outputs_dict = {"var_name": "output_var", "hbm_address": 43}
            ones_dict = {"var_name": "ones_var", "hbm_address": 44}
            twiddle_dict = {"var_name": "twiddle_var", "hbm_address": 45}

            # Prepare test data
            test_data = {
                "keygens": [keygens_dict],
                "inputs": [inputs_dict],
                "outputs": [outputs_dict],
                "metadata": {
                    "ones": [ones_dict],
                    "twid": [twiddle_dict],
                },
            }

            # Create the MemInfo with the test data
            mem_info = MemInfo(**test_data)

            # Call the method
            result = mem_info.as_dict()

            # Verify result structure
            self.assertIn("keygens", result)
            self.assertIn("inputs", result)
            self.assertIn("outputs", result)
            self.assertIn("metadata", result)

            # Verify values
            self.assertEqual(result["keygens"], [keygens_dict])
            self.assertEqual(result["inputs"], [inputs_dict])
            self.assertEqual(result["outputs"], [outputs_dict])
            self.assertIn("ones", result["metadata"])
            self.assertEqual(result["metadata"]["ones"], [ones_dict])

    def test_validate_valid(self):
        """@brief Test validation with valid data."""

        ones_dict = {"var_name": "ones_var", "hbm_address": 44}
        twiddle_dict = {"var_name": "twiddle_var", "hbm_address": 45}

        twiddle_list = [twiddle_dict for _ in range(MemoryModel.MAX_TWIDDLE_META_VARS_PER_SEGMENT)]

        # Create metadata dictionary for initialization
        metadata_dict = {
            "ones": [ones_dict],
            "twid": twiddle_list,
        }

        # Initialize without validation to set up the test
        mem_info = MemInfo(metadata=metadata_dict)

        # Now explicitly call validate which we want to test
        mem_info.validate()  # Should not raise any exceptions

    def test_validate_twiddle_mismatch(self):
        """@brief Test validation with mismatched twiddle count."""

        ones_dict = {"var_name": "ones_var", "hbm_address": 44}
        twiddle_dict = {"var_name": "twiddle_var", "hbm_address": 45}

        # Create metadata dictionary for initialization
        metadata_dict = {
            "ones": [ones_dict],
            "twid": [twiddle_dict],
        }

        # Call MemInfo initialization with metadata
        with patch(
            "assembler.memory_model.mem_info.MemoryModel.MAX_TWIDDLE_META_VARS_PER_SEGMENT",
            2,
        ):
            with self.assertRaises(RuntimeError) as context:
                # Initialize without validation to set up the test
                MemInfo(metadata=metadata_dict)

            self.assertIn("Expected 2 times as many twiddles as ones", str(context.exception))

    def test_validate_duplicate_var_name(self):
        """@brief Test validation with duplicate variable names but different HBM addresses."""
        # Create variable dictionaries with duplicate names but different addresses
        intt_aux_dict = {"var_name": "duplicate", "hbm_address": 1}
        ntt_route_dict = {"var_name": "duplicate", "hbm_address": 2}

        # Create metadata dictionary for initialization with the duplicate variables
        metadata_dict = {
            "ones": [],
            "twid": [],
            "intt_auxiliary_table": [intt_aux_dict],
            "ntt_routing_table": [ntt_route_dict],
            "ntt_auxiliary_table": [],
            "intt_routing_table": [],
        }

        # Initialize MemInfo with the metadata containing duplicates
        with self.assertRaises(RuntimeError) as context:
            MemInfo(metadata=metadata_dict)

            self.assertIn('Variable "duplicate" already allocated', str(context.exception))


class TestUpdateMemoryModelWithMemInfo(unittest.TestCase):
    """@brief Tests for the updateMemoryModelWithMemInfo function."""

    def setUp(self):
        """@brief Set up common test fixtures."""
        # Create mock MemoryModel
        self.mock_mem_model = MagicMock()
        self.mock_mem_model.retrieveVarAdd = MagicMock()

        # Create mock MemInfo
        self.mock_mem_info = MagicMock()

        # Group all mock variables in a dictionary
        self.vars = {
            "input": MagicMock(var_name="input_var", hbm_address=1),
            "output": MagicMock(var_name="output_var", hbm_address=2),
            "ones": MagicMock(var_name="ones_var", hbm_address=3),
            "ntt_aux": MagicMock(var_name="ntt_aux", hbm_address=4),
            "ntt_route": MagicMock(var_name="ntt_route", hbm_address=5),
            "intt_aux": MagicMock(var_name="intt_aux", hbm_address=6),
            "intt_route": MagicMock(var_name="intt_route", hbm_address=7),
            "twiddle": MagicMock(var_name="twiddle_var", hbm_address=8),
            "keygen_seed": MagicMock(var_name="keygen_seed", hbm_address=9),
        }

        # Set up MemInfo
        self.mock_mem_info.inputs = [self.vars["input"]]
        self.mock_mem_info.outputs = [self.vars["output"]]

        # Set up metadata
        self.mock_metadata = MagicMock()
        self.mock_metadata.ones = [self.vars["ones"]]
        self.mock_metadata.ntt_auxiliary_table = [self.vars["ntt_aux"]]
        self.mock_metadata.ntt_routing_table = [self.vars["ntt_route"]]
        self.mock_metadata.intt_auxiliary_table = [self.vars["intt_aux"]]
        self.mock_metadata.intt_routing_table = [self.vars["intt_route"]]
        self.mock_metadata.twiddle = [self.vars["twiddle"]]
        self.mock_metadata.keygen_seeds = [self.vars["keygen_seed"]]

        self.mock_mem_info.metadata = self.mock_metadata

    def test_update_memory_model_inputs(self):
        """@brief Test updating memory model with input variables."""
        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_allocate:
            updateMemoryModelWithMemInfo(self.mock_mem_model, self.mock_mem_info)

            # Verify input variables were allocated
            mock_allocate.assert_any_call(self.mock_mem_model, self.vars["input"])

    def test_update_memory_model_outputs(self):
        """@brief Test updating memory model with output variables."""
        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_allocate:
            updateMemoryModelWithMemInfo(self.mock_mem_model, self.mock_mem_info)

            # Verify output variables were allocated and added to output_variables
            mock_allocate.assert_any_call(self.mock_mem_model, self.vars["output"])
            self.mock_mem_model.output_variables.push.assert_called_once_with("output_var", None)

    def test_update_memory_model_metadata(self):
        """@brief Test updating memory model with metadata variables."""
        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_allocate:
            updateMemoryModelWithMemInfo(self.mock_mem_model, self.mock_mem_info)

            # Verify metadata variables were retrieved, allocated and added to their respective lists
            self.mock_mem_model.retrieveVarAdd.assert_has_calls(
                [
                    call("ones_var"),
                    call("ntt_aux"),
                    call("ntt_route"),
                    call("intt_aux"),
                    call("intt_route"),
                    call("twiddle_var"),
                    call("keygen_seed"),
                ],
                any_order=True,
            )

            mock_allocate.assert_has_calls(
                [
                    call(self.mock_mem_model, self.vars["ones"]),
                    call(self.mock_mem_model, self.vars["ntt_aux"]),
                    call(self.mock_mem_model, self.vars["ntt_route"]),
                    call(self.mock_mem_model, self.vars["intt_aux"]),
                    call(self.mock_mem_model, self.vars["intt_route"]),
                    call(self.mock_mem_model, self.vars["twiddle"]),
                    call(self.mock_mem_model, self.vars["keygen_seed"]),
                ],
                any_order=True,
            )

            self.mock_mem_model.add_meta_ones_var.assert_called_once_with("ones_var")
            self.assertEqual(self.mock_mem_model.meta_ntt_aux_table, "ntt_aux")
            self.assertEqual(self.mock_mem_model.meta_ntt_routing_table, "ntt_route")
            self.assertEqual(self.mock_mem_model.meta_intt_aux_table, "intt_aux")
            self.assertEqual(self.mock_mem_model.meta_intt_routing_table, "intt_route")
            self.mock_mem_model.add_meta_twiddle_var.assert_called_once_with("twiddle_var")
            self.mock_mem_model.add_meta_keygen_seed_var.assert_called_once_with("keygen_seed")


class TestAllocateMemInfoVariable(unittest.TestCase):
    """@brief Tests for the _allocateMemInfoVariable function."""

    def test_allocate_mem_info_variable_success(self):
        """@brief Test successful allocation of a MemInfo variable."""
        # Create mock MemoryModel and variable
        mock_mem_model = MagicMock()
        mock_var_info = MagicMock(var_name="test_var", hbm_address=42)

        # Mock variables dictionary
        mock_mem_model.variables = {"test_var": MagicMock(hbm_address=-1)}

        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_function:
            # Make it actually call the real function - simplified without lambda
            mock_function.original = _allocateMemInfoVariable
            mock_function.side_effect = mock_function.original

            mock_function(mock_mem_model, mock_var_info)

            # Verify the variable was allocated
            mock_mem_model.hbm.allocateForce.assert_called_once_with(42, mock_mem_model.variables["test_var"])

    def test_allocate_mem_info_variable_not_in_model(self):
        """@brief Test allocation when the variable is not in the memory model."""
        # Create mock MemoryModel and variable
        mock_mem_model = MagicMock()
        mock_var_info = MagicMock(var_name="missing_var", hbm_address=42)

        # Mock variables dictionary (missing the variable)
        mock_mem_model.variables = {}

        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_function:
            # Make it actually call the real function - simplified without lambda
            mock_function.original = _allocateMemInfoVariable
            mock_function.side_effect = mock_function.original

            # Verify exception is raised
            with self.assertRaises(RuntimeError) as context:
                mock_function(mock_mem_model, mock_var_info)

            self.assertIn("Variable missing_var not in memory model", str(context.exception))

    def test_allocate_mem_info_variable_mismatch(self):
        """@brief Test allocation when the variable has a different HBM address."""
        # Create mock MemoryModel and variable
        mock_mem_model = MagicMock()
        mock_var_info = MagicMock(var_name="test_var", hbm_address=42)

        # Mock variables dictionary with a variable that already has a different HBM address
        mock_mem_model.variables = {"test_var": MagicMock(hbm_address=24)}

        # Call the function
        with patch("assembler.memory_model.mem_info._allocateMemInfoVariable") as mock_function:
            # Make it actually call the real function - simplified without lambda
            mock_function.original = _allocateMemInfoVariable
            mock_function.side_effect = mock_function.original

            # Verify exception is raised
            with self.assertRaises(RuntimeError) as context:
                mock_function(mock_mem_model, mock_var_info)

            self.assertIn(
                "Variable test_var already allocated in HBM address 24",
                str(context.exception),
            )


if __name__ == "__main__":
    unittest.main()
