# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_kernel_op.py
@brief Unit tests for the KernelOp class
"""

from unittest.mock import patch

import pytest
from linker.kern_trace.context_config import ContextConfig
from linker.kern_trace.kern_var import KernVar
from linker.kern_trace.kernel_op import KernelOp


class TestKernelOp:
    """
    @class TestKernelOp
    @brief Test cases for the KernelOp class
    """

    def _create_test_context_config(self):
        """
        @brief Helper method to create a test ContextConfig
        """
        return ContextConfig(scheme="CKKS", poly_mod_degree=8192, keyrns_terms=2)

    def _create_test_kern_args(self):
        """
        @brief Helper method to create test kernel arguments
        """
        return ["input-8192-2", "output-8192-2"]

    def test_init_with_valid_params(self):
        """
        @brief Test initialization of KernelOp with valid parameters
        """
        # Arrange
        context_config = self._create_test_context_config()
        kern_args = self._create_test_kern_args()

        # Act
        kernel_op = KernelOp("add", context_config, kern_args)

        # Assert
        assert kernel_op.name == "add"
        assert kernel_op.scheme == "CKKS"
        assert kernel_op.poly_modulus_degree == 8192
        assert kernel_op.keyrns_terms == 2
        assert kernel_op.level == 2  # From the level in test args
        assert len(kernel_op.kern_vars) == 2
        assert isinstance(kernel_op.kern_vars[0], KernVar)
        assert isinstance(kernel_op.kern_vars[1], KernVar)
        assert kernel_op.expected_in_kern_file_name == "ckks_add_8192_l2_m2"

    def test_init_with_invalid_kernel_operation_name(self):
        """
        @brief Test initialization with invalid kernel operation name
        """
        # Arrange
        context_config = self._create_test_context_config()
        kern_args = self._create_test_kern_args()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid kernel operation name"):
            KernelOp("invalid_op", context_config, kern_args)

    def test_init_with_invalid_encryption_scheme(self):
        """
        @brief Test initialization with invalid encryption scheme
        """
        # Arrange
        invalid_context = ContextConfig(scheme="INVALID", poly_mod_degree=8192, keyrns_terms=2)
        kern_args = self._create_test_kern_args()

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid encryption scheme"):
            KernelOp("add", invalid_context, kern_args)

    def test_init_with_insufficient_arguments(self):
        """
        @brief Test initialization with insufficient arguments
        """
        # Arrange
        context_config = self._create_test_context_config()
        insufficient_args = ["input-8192-2"]  # Only one argument

        # Act & Assert
        with pytest.raises(ValueError, match="at least two arguments"):
            KernelOp("add", context_config, insufficient_args)

    def test_get_kern_var_objs(self):
        """
        @brief Test get_kern_var_objs method
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())
        test_var_strs = ["var1-1024-1", "var2-2048-2"]

        # Act - Using the private method for testing
        with patch("linker.kern_trace.kern_var.KernVar.from_string") as mock_from_string:
            mock_from_string.side_effect = [
                KernVar("var1", 1024, 1),
                KernVar("var2", 2048, 2),
            ]
            result = kernel_op.get_kern_var_objs(test_var_strs)

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], KernVar)
        assert isinstance(result[1], KernVar)
        assert result[0].label == "var1"
        assert result[1].label == "var2"

    def test_get_kern_var_objs_with_empty_list(self):
        """
        @brief Test get_kern_var_objs with empty list
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Act
        result = kernel_op.get_kern_var_objs([])

        # Assert
        assert result == []

    def test_get_kern_var_objs_with_invalid_var_string(self):
        """
        @brief Test get_kern_var_objs with invalid variable string format
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())
        invalid_var_strs = ["invalid-format"]

        # Act & Assert
        with patch("linker.kern_trace.kern_var.KernVar.from_string") as mock_from_string:
            mock_from_string.side_effect = ValueError("Invalid format")
            with pytest.raises(ValueError):
                kernel_op.get_kern_var_objs(invalid_var_strs)

    def test_get_kern_var_objs_integration_without_mock(self):
        """
        @brief Test get_kern_var_objs without mocking (integration test)
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())
        test_var_strs = ["var1-1024-1", "var2-2048-2"]

        # Act
        result = kernel_op.get_kern_var_objs(test_var_strs)

        # Assert
        assert len(result) == 2
        assert all(isinstance(v, KernVar) for v in result)

    def test_get_level(self):
        """
        @brief Test get_level method
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Create test KernVar objects
        test_vars = [KernVar("var1", 1024, 1), KernVar("var2", 2048, 3)]

        # Act - Using the private method for testing
        result = kernel_op.get_level(test_vars)

        # Assert
        assert result == 3  # Should use the level from the second variable

    def test_get_level_with_single_var(self):
        """
        @brief Test get_level method with a single variable
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Create test KernVar objects
        test_vars = [KernVar("var1", 1024, 2)]

        # Act - Using the private method for testing
        result = kernel_op.get_level(test_vars)

        # Assert
        assert result == 2  # Should use the level from the only variable

    def test_get_level_with_empty_vars(self):
        """
        @brief Test get_level method with empty variables list
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Act & Assert
        with pytest.raises(ValueError, match="at least one variable"):
            kernel_op.get_level([])

    def test_str_representation(self):
        """
        @brief Test string representation of KernelOp
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Act
        result = str(kernel_op)

        # Assert
        assert "KernelOp" in result
        assert "add" in result

    def test_property_kern_vars(self):
        """
        @brief Test kern_vars property
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), self._create_test_kern_args())

        # Act
        result = kernel_op.kern_vars

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], KernVar)
        assert isinstance(result[1], KernVar)
        assert result[0].label == "input"
        assert result[1].label == "output"

    def test_property_name(self):
        """
        @brief Test name property
        """
        # Arrange
        kernel_op = KernelOp("mul", self._create_test_context_config(), self._create_test_kern_args())

        # Act
        result = kernel_op.name

        # Assert
        assert result == "mul"

    def test_property_scheme(self):
        """
        @brief Test scheme property
        """
        # Arrange
        context = ContextConfig(scheme="BFV", poly_mod_degree=4096, keyrns_terms=1)
        kernel_op = KernelOp("add", context, self._create_test_kern_args())

        # Act
        result = kernel_op.scheme

        # Assert
        assert result == "BFV"

    def test_property_poly_modulus_degree(self):
        """
        @brief Test poly_modulus_degree property
        """
        # Arrange
        context = ContextConfig(scheme="CKKS", poly_mod_degree=16384, keyrns_terms=2)
        kernel_op = KernelOp("add", context, self._create_test_kern_args())

        # Act
        result = kernel_op.poly_modulus_degree

        # Assert
        assert result == 16384

    def test_property_keyrns_terms(self):
        """
        @brief Test keyrns_terms property
        """
        # Arrange
        context = ContextConfig(scheme="CKKS", poly_mod_degree=8192, keyrns_terms=3)
        kernel_op = KernelOp("add", context, self._create_test_kern_args())

        # Act
        result = kernel_op.keyrns_terms

        # Assert
        assert result == 3

    def test_property_level(self):
        """
        @brief Test level property
        """
        # Arrange
        kernel_op = KernelOp("add", self._create_test_context_config(), ["var1-8192-4", "var2-8192-4"])

        # Act
        result = kernel_op.level

        # Assert
        assert result == 4

    def test_property_expected_in_kern_file_name(self):
        """
        @brief Test expected_in_kern_file_name property
        """
        # Arrange
        context = ContextConfig(scheme="BGV", poly_mod_degree=2048, keyrns_terms=1)
        kernel_op = KernelOp("mul", context, ["var1-2048-5", "var2-2048-5"])

        # Act
        result = kernel_op.expected_in_kern_file_name

        # Assert
        assert result == "bgv_mul_2048_l5_m1"

    def test_case_insensitivity_of_operation_name(self):
        """
        @brief Test that operation names are case-insensitive
        """
        # Arrange
        context_config = self._create_test_context_config()
        kern_args = self._create_test_kern_args()

        # Act
        kernel_op = KernelOp("ADD", context_config, kern_args)  # Uppercase operation name

        # Assert
        assert kernel_op.name == "ADD"
        assert kernel_op.expected_in_kern_file_name == "ckks_add_8192_l2_m2"  # Note: lowercase in file name

    def test_case_insensitivity_of_scheme(self):
        """
        @brief Test that scheme names are case-insensitive
        """
        # Arrange
        context = ContextConfig(scheme="ckks", poly_mod_degree=8192, keyrns_terms=2)  # Lowercase scheme
        kern_args = self._create_test_kern_args()

        # Act
        kernel_op = KernelOp("add", context, kern_args)

        # Assert
        assert kernel_op.scheme == "ckks"
        assert kernel_op.expected_in_kern_file_name == "ckks_add_8192_l2_m2"
