# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@brief This module provides functionality to load different types of instruction kernels
"""

import copy
from typing import Any

from assembler.common import dinst
from linker import instructions
from linker.instructions import cinst, minst, xinst


class Loader:
    """
    @class Loader
    @brief A class that provides methods to load different types of instruction kernels.
    """

    # Class-level file cache
    _file_cache: dict[tuple, Any] = {}

    @classmethod
    def flush_cache(cls):
        """
        @brief Clears the file loading cache.
        """
        cls._file_cache.clear()

    @classmethod
    def load_minst_kernel(cls, line_iter) -> list:
        """
        @brief Loads MInstruction kernel from an iterator of lines.

        @param line_iter An iterator over lines of MInstruction strings.
        @return A list of MInstruction objects.
        @throws RuntimeError If a line cannot be parsed into an MInstruction.
        """
        retval: list = []
        for idx, s_line in enumerate(line_iter):
            minstr = instructions.create_from_str_line(s_line, minst.factory())
            if not minstr:
                raise RuntimeError(f"Error parsing line {idx + 1}: {s_line}")
            retval.append(minstr)
        return retval

    @classmethod
    def load_minst_kernel_from_file(cls, filename: str, use_cache: bool = True) -> list:
        """
        @brief Loads MInstruction kernel from a file.

        @param filename The file containing MInstruction strings.
        @param use_cache Whether to use cached results if available.
        @return A list of MInstruction objects.
        @throws RuntimeError If an error occurs while loading the file.
        """
        cache_key = (filename, "minst")
        if use_cache and cache_key in cls._file_cache:
            return copy.deepcopy(cls._file_cache[cache_key])

        with open(filename, encoding="utf-8") as kernel_minsts:
            try:
                result = cls.load_minst_kernel(kernel_minsts)
                if use_cache:
                    cls._file_cache[cache_key] = result
                return copy.deepcopy(result)
            except Exception as e:
                raise RuntimeError(f'Error occurred loading file "{filename}"') from e

    @classmethod
    def load_cinst_kernel(cls, line_iter) -> list:
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

    @classmethod
    def load_cinst_kernel_from_file(cls, filename: str, use_cache: bool = True) -> list:
        """
        @brief Loads CInstruction kernel from a file.

        @param filename The file containing CInstruction strings.
        @param use_cache Whether to use cached results if available.
        @return A list of CInstruction objects.
        @throws RuntimeError If an error occurs while loading the file.
        """
        cache_key = (filename, "cinst")
        if use_cache and cache_key in cls._file_cache:
            return copy.deepcopy(cls._file_cache[cache_key])

        with open(filename, encoding="utf-8") as kernel_cinsts:
            try:
                result = cls.load_cinst_kernel(kernel_cinsts)
                if use_cache:
                    cls._file_cache[cache_key] = result
                return copy.deepcopy(result)
            except Exception as e:
                raise RuntimeError(f'Error occurred loading file "{filename}"') from e

    @classmethod
    def load_xinst_kernel(cls, line_iter) -> list:
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

    @classmethod
    def load_xinst_kernel_from_file(cls, filename: str, use_cache: bool = True) -> list:
        """
        @brief Loads XInstruction kernel from a file.

        @param filename The file containing XInstruction strings.
        @param use_cache Whether to use cached results if available.
        @return A list of XInstruction objects.
        @throws RuntimeError If an error occurs while loading the file.
        """
        cache_key = (filename, "xinst")
        if use_cache and cache_key in cls._file_cache:
            return copy.deepcopy(cls._file_cache[cache_key])

        with open(filename, encoding="utf-8") as kernel_xinsts:
            try:
                result = cls.load_xinst_kernel(kernel_xinsts)
                if use_cache:
                    cls._file_cache[cache_key] = result
                return copy.deepcopy(result)
            except Exception as e:
                raise RuntimeError(f'Error occurred loading file "{filename}"') from e

    @classmethod
    def load_dinst_kernel(cls, line_iter) -> list:
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

    @classmethod
    def load_dinst_kernel_from_file(cls, filename: str, use_cache: bool = True) -> list:
        """
        @brief Loads DInstruction kernel from a file.

        @param filename The file containing DInstruction strings.
        @param use_cache Whether to use cached results if available.
        @return A list of DInstruction objects.
        @throws RuntimeError If an error occurs while loading the file.
        """
        cache_key = (filename, "dinst")
        if use_cache and cache_key in cls._file_cache:
            return copy.deepcopy(cls._file_cache[cache_key])

        with open(filename, encoding="utf-8") as kernel_dinsts:
            try:
                result = cls.load_dinst_kernel(kernel_dinsts)
                if use_cache:
                    cls._file_cache[cache_key] = result
                return copy.deepcopy(result)
            except Exception as e:
                raise RuntimeError(f'Error occurred loading file "{filename}"') from e
