# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""Module for defining constants and enums used in the kernel generator"""
from enum import Enum


class LoopKey(Enum):
    """Sort keys for PIsaOp instructions"""

    RNS = "rns"
    PART = "part"
    UNIT = "unit"

    @classmethod
    def from_str(cls, value: str) -> "LoopKey":
        """Convert a string to a LoopKey enum"""
        if value is None:
            raise ValueError("LoopKey cannot be None")
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"Invalid LoopKey: {value}") from None
