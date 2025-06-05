#! /usr/bin/env python3
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

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
from kernel_optimization.loops import loop_interchange
from const.options import LoopKey


def parse_args():
    """Parse arguments from the commandline"""
    parser = argparse.ArgumentParser(description="Kernel Graph Parser")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable Debug Print")
    parser.add_argument(
        "-t", "--target", nargs="*", default=[], help="List of high_op names"
    )
    parser.add_argument(
        "-p",
        "--primary",
        type=LoopKey,
        default=LoopKey.PART,
        help="Primary key for loop interchange (default: PART, options: RNS, PART))",
    )
    parser.add_argument(
        "-s",
        "--secondary",
        type=LoopKey,
        default=LoopKey.RNS,
        help="Secondary key for loop interchange (default: RNS, Options: RNS, PART)",
    )
    parsed_args = parser.parse_args()
    # verify that primary and secondary keys are valid and not the same
    valid_keys = set(LoopKey)
    if parsed_args.primary not in valid_keys or parsed_args.secondary not in valid_keys:
        valid_names = ", ".join(key.name for key in LoopKey)
        raise ValueError(
            f"Invalid primary or secondary key. Valid options are: {valid_names}"
        )
    if parsed_args.primary == parsed_args.secondary:
        raise ValueError("Primary and secondary keys cannot be the same.")
    return parser.parse_args()


def main(args):
    """Main function to read input and parse each line with KernelParser."""
    input_lines = sys.stdin.read().strip().splitlines()
    valid_kernels = []

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
        print(
            f"# Reordered targets {args.target} with primary key {args.primary} and secondary key {args.secondary}"
        )
        for kernel in valid_kernels:
            if args.target and any(target in str(kernel) for target in args.target):
                kernel = loop_interchange(
                    kernel.to_pisa(),
                    primary_key=args.primary,
                    secondary_key=args.secondary,
                )
            for pisa in kernel:
                print(pisa)


if __name__ == "__main__":
    cmdline_args = parse_args()
    main(cmdline_args)
