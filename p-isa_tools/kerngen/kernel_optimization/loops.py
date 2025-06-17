# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""Module for loop interchange optimization in P-ISA operations"""

import re
from const.options import LoopKey
from high_parser.pisa_operations import PIsaOp, Comment


def loop_interchange(
    pisa_list: list[PIsaOp],
    primary_key: LoopKey | None = LoopKey.PART,
    secondary_key: LoopKey | None = LoopKey.RNS,
) -> list[PIsaOp]:
    """Batch pisa_list into groups and sort them by primary and optional secondary keys.

    Args:
        pisa_list: List of PIsaOp instructions
        primary_key: Primary sort criterion from SortKey enum
        secondary_key: Optional secondary sort criterion from SortKey enum

    Returns:
        List of processed PIsaOp instructions

    Raises:
        ValueError: If invalid sort key values provided
    """
    if primary_key is None and secondary_key is None:
        return pisa_list

    def get_sort_value(pisa: PIsaOp, key: LoopKey) -> int:
        match key:
            case LoopKey.RNS:
                return pisa.q
            case LoopKey.PART:
                match = re.search(r"_(\d+)_", str(pisa))
                return int(match[1]) if match else 0
            case LoopKey.UNIT:
                match = re.search(r"_(\d+),", str(pisa))
                return int(match[1]) if match else 0
            case _:
                raise ValueError(f"Invalid sort key value: {key}")

    def get_sort_key(pisa: PIsaOp) -> tuple:
        primary_value = get_sort_value(pisa, primary_key)
        if secondary_key:
            secondary_value = get_sort_value(pisa, secondary_key)
            return (primary_value, secondary_value)
        return (primary_value,)

    # Filter out comments
    pisa_list_wo_comments = [p for p in pisa_list if not isinstance(p, Comment)]
    # Sort based on primary and optional secondary keys
    pisa_list_wo_comments.sort(key=get_sort_key)
    return pisa_list_wo_comments
