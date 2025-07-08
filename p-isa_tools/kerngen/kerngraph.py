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
from kernel_parser.parser import KernelParser
from kernel_optimization.loops import loop_interchange, split_by_reorderable
from const.options import LoopKey
from pisa_generators.basic import mixed_to_pisa_ops
from high_parser.config import Config


def parse_args():
    """Parse arguments from the commandline"""
    parser = argparse.ArgumentParser(description="Kernel Graph Parser")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable Debug Print")
    parser.add_argument(
        "-l", "--legacy", action="store_true", help="Enable Legacy Mode"
    )
    parser.add_argument(
        "-t",
        "--target",
        nargs="*",
        default=[],
        # Composition high ops such are ntt, mod, and relin are not currently supported
        choices=["add", "sub", "mul", "muli", "copy", "ntt", "intt", "mod"],
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
        choices=list(LoopKey) + list([None]),
        help="Secondary key for loop interchange (default: None, Options: RNS, PART)",
    )
    parsed_args = parser.parse_args()
    # verify that primary and secondary keys are  not the same
    if parsed_args.primary == parsed_args.secondary:
        raise ValueError("Primary and secondary keys cannot be the same.")
    return parser.parse_args()


def main(args):
    """Main function to read input and parse each line with KernelParser."""
    input_lines = sys.stdin.read().strip().splitlines()
    valid_kernels = []
    Config.legacy_mode = args.legacy

    for line in input_lines:
        try:
            kernel = KernelParser.parse_kernel(line)
            valid_kernels.append(kernel)
        except ValueError as e:
            if args.debug:
                print(f"Error parsing line: {line}\nReason: {e}")
            continue  # Skip invalid lines

    if not valid_kernels:
        print("No valid kernel strings were parsed.")
    else:
        if args.debug:
            print(
                f"# Reordered targets {args.target} with primary key {args.primary} and secondary key {args.secondary}"
            )
        for kernel in valid_kernels:
            if args.target and any(
                target.lower() in str(kernel).lower() for target in args.target
            ):
                reorderable, non_reorderable = split_by_reorderable(kernel.to_pisa())
                kernel = non_reorderable
                kernel.append(
                    loop_interchange(
                        reorderable,
                        primary_key=args.primary,
                        secondary_key=args.secondary,
                    )
                )

                for pisa in mixed_to_pisa_ops(kernel):
                    print(pisa)
            else:
                for pisa in kernel.to_pisa():
                    print(pisa)


if __name__ == "__main__":
    cmdline_args = parse_args()
    main(cmdline_args)
