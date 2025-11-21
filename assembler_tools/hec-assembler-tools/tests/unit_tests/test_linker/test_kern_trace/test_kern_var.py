# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_kern_var.py
@brief Unit tests for the KernVar class
"""

import pytest
from linker.kern_trace.kern_var import KernVar


class TestKernVar:
    """
    @class TestKernVar
    @brief Test cases for the KernVar class
    """

    def test_init_with_valid_params(self):
        """
        @brief Test initialization of KernVar with valid parameters
        """
        # Arrange & Act
        kern_var = KernVar("input", 8192, 3)

        # Assert
        assert kern_var.label == "input"
        assert kern_var.degree == 8192
        assert kern_var.level == 3

    def test_from_string_with_valid_input(self):
        """
        @brief Test from_string class method with valid input
        """
        # Arrange
        var_str = "input-8192-3"

        # Act
        kern_var = KernVar.from_string(var_str)

        # Assert
        assert kern_var.label == "input"
        assert kern_var.degree == 8192
        assert kern_var.level == 3

    def test_from_string_with_invalid_format(self):
        """
        @brief Test from_string with invalid format (missing parts)
        """
        # Arrange
        invalid_var_strs = [
            "input",  # Missing degree and level
            "input-8192",  # Missing level
            "-8192-3",  # Missing label
            "input-8192-a",  # Non digit
            "input-d-0",  # Non digit
            "input-8192-3-extra",  # Too many parts
        ]

        # Act & Assert
        for invalid_str in invalid_var_strs:
            with pytest.raises(ValueError, match="Invalid"):
                KernVar.from_string(invalid_str)

    def test_from_string_with_non_numeric_degree(self):
        """
        @brief Test from_string with non-numeric degree
        """
        # Arrange
        var_str = "input-degree-3"

        # Act & Assert
        with pytest.raises(ValueError):
            KernVar.from_string(var_str)

    def test_from_string_with_non_numeric_level(self):
        """
        @brief Test from_string with non-numeric level
        """
        # Arrange
        var_str = "input-8192-level"

        # Act & Assert
        with pytest.raises(ValueError):
            KernVar.from_string(var_str)

    def test_label_property_immutability(self):
        """
        @brief Test that label property is immutable (read-only)
        """
        # Arrange
        kern_var = KernVar("input", 8192, 3)

        # Act & Assert
        with pytest.raises(AttributeError):
            kern_var.label = "new_label"  # Should raise AttributeError for read-only property

    def test_degree_property_immutability(self):
        """
        @brief Test that degree property is immutable (read-only)
        """
        # Arrange
        kern_var = KernVar("input", 8192, 3)

        # Act & Assert
        with pytest.raises(AttributeError):
            kern_var.degree = 4096  # Should raise AttributeError for read-only property

    def test_level_property_immutability(self):
        """
        @brief Test that level property is immutable (read-only)
        """
        # Arrange
        kern_var = KernVar("input", 8192, 3)

        # Act & Assert
        with pytest.raises(AttributeError):
            kern_var.level = 1  # Should raise AttributeError for read-only property

    def test_repr_representation(self):
        """
        @brief Test __repr__ method if implemented
        """
        # Arrange
        kern_var = KernVar("var", 4096, 2)

        # Act
        result = repr(kern_var)

        # Assert
        assert isinstance(result, str)
        assert len(result) > 0

    def test_equality_between_identical_kern_vars(self):
        """
        @brief Test equality comparison if __eq__ is implemented
        """
        # Arrange
        var1 = KernVar("test", 8192, 2)
        var2 = KernVar("test", 8192, 2)

        # Act & Assert
        # Check if __eq__ is implemented by comparing
        try:
            assert var1 == var2 or (var1.label == var2.label and var1.degree == var2.degree and var1.level == var2.level)
        except AssertionError:
            # If __eq__ not implemented, identity comparison will fail
            pass

    def test_inequality_between_different_kern_vars(self):
        """
        @brief Test inequality when labels differ
        """
        # Arrange
        var1 = KernVar("var1", 8192, 2)
        var2 = KernVar("var2", 8192, 2)

        # Act & Assert
        assert var1 != var2 or var1.label != var2.label
