#! /usr/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.

"""
kerngraph.py

This script provides a command-line tool for parsing kernel strings from standard input using the KernelParser class.
Future improvements may include graph representation of the parsed kernels and optimization.

Functions:
    parse_args():
        Parses command-line arguments.
        Returns:
            argparse.Namespace: Parsed arguments including debug flag.

    main(args):
        Reads lines from standard input, parses each line as a kernel string using KernelParser,
        and prints the successfully parsed kernel objects. If parsing fails for a line, an error
        message is printed if debug mode is enabled.

Usage:
    Run the script and provide kernel strings via standard input. Use the '-d' or '--debug' flag
    to enable debug output for parsing errors.

Example:
    $ cat bgv.add.high | ./kerngen.py | ./kerngraph.py
"""

import argparse
import sys

from const.options import LoopKey
from high_parser.config import Config
from kernel_optimization.loop_ordering_lookup import get_loop_order
from kernel_optimization.loops import loop_interchange, reuse_rns_label, split_by_reorderable
from kernel_parser.parser import KernelParser
from pisa_generators.basic import mixed_to_pisa_ops


def parse_args():
    """Parse arguments from the commandline"""
    parser = argparse.ArgumentParser(description="Kernel Graph Parser")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable Debug Print")
    parser.add_argument("-l", "--legacy", action="store_true", help="Enable Legacy Mode")
    parser.add_argument(
        "-t",
        "--target",
        nargs="*",
        default=[],
        # Composition high ops such are ntt, mod, etc.
        choices=["add", "sub", "mul", "muli", "copy", "ntt", "intt", "mod", "relin", "rotate", "rescale"],
        help="List of high_op names",
    )
    parser.add_argument(
        "-p",
        "--primary",
        type=LoopKey,
        default=LoopKey.PART,
        choices=list(LoopKey),
        help="Primary key for loop interchange (default: PART, options: RNS, PART))",
    )
    parser.add_argument(
        "-s",
        "--secondary",
        type=LoopKey,
        default=None,
        choices=list(LoopKey) + [None],
        help="Secondary key for loop interchange (default: None, Options: RNS, PART)",
    )
    parser.add_argument(
        "--optimal",
        action="store_true",
        help="Use optimal primary and secondary loop order based on kernel configuration (overrides -p and -s)",
    )
    parsed_args = parser.parse_args()
    # verify that primary and secondary keys are  not the same
    if not parsed_args.optimal and parsed_args.primary == parsed_args.secondary:
        raise ValueError("Primary and secondary keys cannot be the same.")
    return parsed_args


def get_optimal_loop_order(kernel, debug=False):
    """
    Get optimal loop order for a kernel based on its properties.

    Args:
        kernel: Parsed kernel object
        debug (bool): Enable debug output

    Returns:
        Tuple[LoopKey, LoopKey]: Primary and secondary loop keys, or (None, None) if not found
    """
    try:
        # Extract kernel properties
        scheme = getattr(kernel.context, "scheme", "bgv").lower()
        kernel_name = str(kernel).split("(")[0].lower()
        polyorder = getattr(kernel.context, "poly_order", 16384)
        max_rns = getattr(kernel.context, "max_rns", 3)
        # Get optimal loop order from configuration
        primary_str, secondary_str = get_loop_order(scheme, kernel_name, polyorder, max_rns)
        # Map string values to LoopKey enum
        loop_key_mapping = {"part": LoopKey.PART, "rns": LoopKey.RNS, "null": None}

        primary_key = loop_key_mapping.get(primary_str)
        secondary_key = loop_key_mapping.get(secondary_str)

        if debug:
            print(
                "# Optimal loop order for"
                + f" {scheme}.{kernel_name}: primary={primary_str} ({primary_key}), secondary={secondary_str} ({secondary_key})"
            )

        return primary_key, secondary_key

    except ValueError as e:
        if debug:
            print(f"# Warning: Could not determine optimal loop order for kernel {kernel}: {e}")
        return None, None


def parse_kernels(input_lines, debug=False):
    """Parse kernel strings from input lines."""
    valid_kernels = []
    for line in input_lines:
        try:
            kernel = KernelParser.parse_kernel(line)
            valid_kernels.append(kernel)
        except ValueError as e:
            if debug:
                print(f"Error parsing line: {line}\nReason: {e}")
            continue  # Skip invalid lines
    return valid_kernels


def process_kernel_with_reordering(kernel, args):
    """Process a kernel with reordering optimization."""
    # Determine loop order
    if args.optimal:
        primary_key, secondary_key = get_optimal_loop_order(kernel, args.debug)
    else:
        primary_key = args.primary
        secondary_key = args.secondary

    groups = split_by_reorderable(kernel.to_pisa())
    processed_kernel = []
    for group in groups:
        if group.is_reorderable:
            interchanged_pisa = loop_interchange(group.pisa_list, primary_key=primary_key, secondary_key=secondary_key)

            if ("mod" in args.target) and (primary_key is not None and secondary_key is not None):
                for pisa in mixed_to_pisa_ops(interchanged_pisa):
                    processed_kernel.append(reuse_rns_label(pisa, kernel.context.current_rns))
            else:
                processed_kernel.append(interchanged_pisa)
        else:
            processed_kernel.append(group.pisa_list)

    for pisa in mixed_to_pisa_ops(processed_kernel):
        print(pisa)


def should_apply_reordering(kernel, targets):
    """Check if reordering should be applied to this kernel."""
    return targets and any(target.lower() in str(kernel).lower() for target in targets)


def main(args):
    """Main function to read input and parse each line with KernelParser."""
    input_lines = sys.stdin.read().strip().splitlines()
    Config.legacy_mode = args.legacy

    valid_kernels = parse_kernels(input_lines, args.debug)

    if not valid_kernels:
        print("No valid kernel strings were parsed.")
        return

    if args.debug:
        if args.optimal:
            print(f"# Using optimal loop order configuration for targets {args.target}")
        else:
            print(f"# Reordered targets {args.target} with primary key {args.primary} and secondary key {args.secondary}")

    for kernel in valid_kernels:
        if should_apply_reordering(kernel, args.target):
            process_kernel_with_reordering(kernel, args)
        else:
            for pisa in kernel.to_pisa():
                print(pisa)


if __name__ == "__main__":
    cmdline_args = parse_args()
    main(cmdline_args)
