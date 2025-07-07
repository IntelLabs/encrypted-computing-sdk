# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
This module provides decorator utilities for the assembler.

It contains decorators that enhance class and function behavior,
including property-like decorators for class methods.
"""


# pylint: disable=invalid-name
class classproperty(property):
    """
    A decorator that allows a method to be accessed as a class-level property
    rather than on instances of the class.
    """

    def __get__(self, cls, owner):
        """
        Retrieves the value of the class-level property.

        Args:
            cls: The class that owns the property.
            owner: The owner of the class (ignored in this context).

        Returns:
            The result of calling the decorated function with the class as an argument.
        """
        return self.fget(owner)
