# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for handling kernel variables in trace files."""


class KernVar:
    """
    @brief Class representing a kernel variable in trace files.

    @details This class encapsulates the properties of a kernel variable,
    including its label, degree, and level.
    """

    def __init__(self, label: str, degree: int, level: int):
        """
        @brief Initializes a KernVar instance.

        @param label: The label of the kernel variable.
        @param degree: The polynomial degree of the variable.
        @param level: The current RNS level of the variable.
        """
        self._label = label
        self._degree = degree
        self._level = level

    @classmethod
    def from_string(cls, var_str: str):
        """
        @brief Creates a KernVar instance from a string representation.

        @param var_str: The string representation of the kernel variable in the format "label_degree_level".

        @return KernVar: An instance of KernVar initialized with the parsed values.
        """
        parts = var_str.split("-")
        if len(parts) != 3:
            raise ValueError(f"Invalid kernel variable string format: {var_str}")
        if not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError(
                f"Invalid degree or level in kernel variable string: {var_str}"
            )
        if not parts[0]:
            raise ValueError(f"Invalid label in kernel variable string: {var_str}")

        label = parts[0]
        degree = int(parts[1])
        level = int(parts[2])

        return cls(label, degree, level)

    @property
    def label(self) -> str:
        """
        @brief Returns the label of the kernel variable.

        @return str: The label of the kernel variable.
        """
        return self._label

    @property
    def degree(self) -> int:
        """
        @brief Returns the polynomial degree of the kernel variable.

        @return int: The polynomial degree of the kernel variable.
        """
        return self._degree

    @property
    def level(self) -> int:
        """
        @brief Returns the current RNS level of the kernel variable.

        @return int: The current RNS level of the kernel variable.
        """
        return self._level
