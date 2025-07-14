# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""Module for loop interchange optimization in P-ISA operations"""

import re
from const.options import LoopKey
from high_parser.pisa_operations import PIsaOp, Comment


def remove_comments(pisa_list: list[PIsaOp]) -> list[PIsaOp]:
    """Remove comments from a list of PIsaOp instructions.

    Args:
        pisa_list: List of PIsaOp instructions

    Returns:
        List of PIsaOp instructions without comments
    """
    return [pisa for pisa in pisa_list if not isinstance(pisa, Comment)]


def split_by_reorderable(pisa_list: list[PIsaOp]) -> tuple[list[PIsaOp], list[PIsaOp]]:
    """Split a list of PIsaOp instructions into reorderable and non-reorderable groups.

    Args:
        pisa_list: List of PIsaOp instructions

    Returns:
        Tuple containing two lists:
            - reorderable: Instructions that can be reordered
            - non_reorderable: Instructions that cannot be reordered
    """

    reorderable = []
    non_reorderable = []
    is_reorderable = False

    for pisa in pisa_list:
        # if the pisa is a comment and it contains <reorderable> tag, treat the following pisa as reorderable until a </reorderable> tag is found.
        if isinstance(pisa, Comment):
            if "<reorderable>" in pisa.line:
                is_reorderable = True
            elif "</reorderable>" in pisa.line:
                is_reorderable = False

        if is_reorderable:
            reorderable.append(pisa)
        else:
            non_reorderable.append(pisa)

    # if reoderable is empty, return non_reorderable as reorderable
    if not reorderable:
        reorderable = non_reorderable
        non_reorderable = []
    return remove_comments(reorderable), remove_comments(non_reorderable)


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
    pisa_list_wo_comments = remove_comments(pisa_list)
    # Sort based on primary and optional secondary keys
    pisa_list_wo_comments.sort(key=get_sort_key)
    return pisa_list_wo_comments
