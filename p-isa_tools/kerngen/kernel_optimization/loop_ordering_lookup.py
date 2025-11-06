# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""
Loop order lookup functionality for encrypted computing kernels.

This module provides functionality to determine primary and secondary loop orders
based on scheme, kernel type, polynomial order, and RNS parameters.
"""

import json
from pathlib import Path

LOOP_ORDER_CONFIG = str(Path(__file__).parent.parent.absolute() / "kernel_optimization/loop_order_config.json")


def _parse_range(range_str: str) -> tuple[int, int]:
    """
    Parse a range string like '1-5' or '3' into min, max values.

    Args:
        range_str (str): Range string like '1-5' or '3'

    Returns:
        Tuple[int, int]: (min_value, max_value) inclusive
    """
    if "-" in range_str:
        min_val, max_val = range_str.split("-")
        return int(min_val), int(max_val)
    else:
        val = int(range_str)
        return val, val


def _value_in_range(value: int, range_str: str) -> bool:
    """
    Check if a value falls within a range string.

    Args:
        value (int): Value to check
        range_str (str): Range string like '1-5' or '3'

    Returns:
        bool: True if value is in range
    """
    min_val, max_val = _parse_range(range_str)
    return min_val <= value <= max_val


def get_loop_order(
    scheme: str,
    kernel: str,
    polyorder: int,
    max_rns: int,
) -> tuple[str, str]:
    """
    Get primary and secondary loop order based on configuration.

    Args:
        scheme (str): Encryption scheme ('bgv', 'ckks')
        kernel (str): Kernel type ('add', 'mul', 'muli', 'copy', 'sub',
                     'square', 'ntt', 'intt', 'mod', 'modup', 'relin',
                     'rotate', 'rescale')
        polyorder (int): Polynomial order (16384, 32768, 65536)
        max_rns (int): Maximum RNS value
        config_file (str, optional): Path to configuration file.
                                   Defaults to loop_order_config.json in same directory.

    Returns:
        Tuple[str, str]: Primary and secondary loop order

    Raises:
        FileNotFoundError: If configuration file is not found
        KeyError: If the specified parameters are not found in configuration
        ValueError: If parameters are invalid
    """
    # Validate inputs
    valid_schemes = {"bgv", "ckks"}
    valid_kernels = {"add", "mul", "muli", "copy", "sub", "square", "ntt", "intt", "mod", "modup", "relin", "rotate", "rescale"}
    valid_polyorders = {16384, 32768, 65536}

    scheme = scheme.lower()
    kernel = kernel.lower()

    if scheme not in valid_schemes:
        raise ValueError(f"Invalid scheme '{scheme}'. Must be one of {valid_schemes}")

    if kernel not in valid_kernels:
        raise ValueError(f"Invalid kernel '{kernel}'. Must be one of {valid_kernels}")

    if polyorder not in valid_polyorders:
        raise ValueError(f"Invalid polyorder '{polyorder}'. Must be one of {valid_polyorders}")

    if max_rns < 1:
        raise ValueError(f"Invalid RNS value: max_rns={max_rns}")

    try:
        with open(LOOP_ORDER_CONFIG, encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Configuration file not found: {LOOP_ORDER_CONFIG}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}") from e

    # Lookup configuration with range support
    try:
        scheme_config = config[scheme]
        kernel_config = scheme_config[kernel]
        polyorder_config = kernel_config[str(polyorder)]

        # Find matching max_rns range
        loop_order = None
        for max_rns_range, order_config in polyorder_config.items():
            if _value_in_range(max_rns, max_rns_range):
                loop_order = order_config
                break

        if loop_order is None:
            raise KeyError(f"max_rns={max_rns}")

        return tuple(loop_order)

    except KeyError as e:
        raise KeyError(
            f"Configuration not found for scheme='{scheme}', kernel='{kernel}', "
            f"polyorder={polyorder}, max_rns={max_rns}. "
            f"Missing key: {e}"
        ) from e


def list_available_configurations(config_file: str | None = None) -> dict:
    """
    List all available configurations in the config file.

    Args:
        config_file (str, optional): Path to configuration file.

    Returns:
        dict: The complete configuration structure
    """

    with open(LOOP_ORDER_CONFIG, encoding="utf-8") as f:
        return json.load(f)
