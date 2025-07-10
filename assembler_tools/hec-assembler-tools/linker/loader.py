# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@brief This module provides functionality to load different types of instruction kernels
"""

from linker.instructions import minst
from linker.instructions import cinst
from linker.instructions import xinst
from linker.instructions import dinst
from linker import instructions


def load_minst_kernel(line_iter) -> list:
    """
    @brief Loads MInstruction kernel from an iterator of lines.

    @param line_iter An iterator over lines of MInstruction strings.
    @return A list of MInstruction objects.
    @throws RuntimeError If a line cannot be parsed into an MInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        minstr = instructions.create_from_str_line(s_line, minst.factory())
        if not minstr:
            raise RuntimeError(f"Error parsing line {idx + 1}: {s_line}")
        retval.append(minstr)
    return retval


def load_minst_kernel_from_file(filename: str) -> list:
    """
    @brief Loads MInstruction kernel from a file.

    @param filename The file containing MInstruction strings.
    @return A list of MInstruction objects.
    @throws RuntimeError If an error occurs while loading the file.
    """
    with open(filename, "r", encoding="utf-8") as kernel_minsts:
        try:
            return load_minst_kernel(kernel_minsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e


def load_cinst_kernel(line_iter) -> list:
    """
    @brief Loads CInstruction kernel from an iterator of lines.

    @param line_iter An iterator over lines of CInstruction strings.
    @return A list of CInstruction objects.
    @throws RuntimeError If a line cannot be parsed into a CInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        cinstr = instructions.create_from_str_line(s_line, cinst.factory())
        if not cinstr:
            raise RuntimeError(f"Error parsing line {idx + 1}: {s_line}")
        retval.append(cinstr)
    return retval


def load_cinst_kernel_from_file(filename: str) -> list:
    """
    @brief Loads CInstruction kernel from a file.

    @param filename The file containing CInstruction strings.
    @return A list of CInstruction objects.
    @throws RuntimeError If an error occurs while loading the file.
    """
    with open(filename, "r", encoding="utf-8") as kernel_cinsts:
        try:
            return load_cinst_kernel(kernel_cinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e


def load_xinst_kernel(line_iter) -> list:
    """
    @brief Loads XInstruction kernel from an iterator of lines.

    @param line_iter An iterator over lines of XInstruction strings.
    @return A list of XInstruction objects.
    @throws RuntimeError If a line cannot be parsed into an XInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        xinstr = instructions.create_from_str_line(s_line, xinst.factory())
        if not xinstr:
            raise RuntimeError(f"Error parsing line {idx + 1}: {s_line}")
        retval.append(xinstr)
    return retval


def load_xinst_kernel_from_file(filename: str) -> list:
    """
    @brief Loads XInstruction kernel from a file.

    @param filename The file containing XInstruction strings.
    @return A list of XInstruction objects.
    @throws RuntimeError If an error occurs while loading the file.
    """
    with open(filename, "r", encoding="utf-8") as kernel_xinsts:
        try:
            return load_xinst_kernel(kernel_xinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e


def load_dinst_kernel(line_iter) -> list:
    """
    @brief Loads DInstruction kernel from an iterator of lines.

    @param line_iter An iterator over lines of DInstruction strings.
    @return A list of DInstruction objects.
    @throws RuntimeError If a line cannot be parsed into an DInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        dinstr = dinst.create_from_mem_line(s_line)
        if not dinstr:
            raise RuntimeError(f"Error parsing line {idx + 1}: {s_line}")
        retval.append(dinstr)

    return retval


def load_dinst_kernel_from_file(filename: str) -> list:
    """
    @brief Loads DInstruction kernel from a file.

    @param filename The file containing DInstruction strings.
    @return A list of DInstruction objects.
    @throws RuntimeError If an error occurs while loading the file.
    """
    with open(filename, "r", encoding="utf-8") as kernel_dinsts:
        try:
            return load_dinst_kernel(kernel_dinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e
