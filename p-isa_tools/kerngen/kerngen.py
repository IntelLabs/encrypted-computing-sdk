#! /usr/bin/env python3

# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module for generating p-isa kernels"""

import argparse
import sys
from typing import Iterable

from high_parser.parser import Parser
from high_parser.config import Config


def parse_args():
    """Parse arguments from the commandline"""
    parser = argparse.ArgumentParser(description="Kernel Generator")
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="disable comments in output"
    )
    parser.add_argument(
        "-l", "--legacy", action="store_true", help="enable legacy mode"
    )
    return parser.parse_args()


def to_string_block(iterable: Iterable[str], *, ignore_comments: bool) -> str:
    """helper to string block"""
    strs = map(str, iterable)
    if ignore_comments is True:
        return "\n".join(i for i in strs if not i.rstrip().startswith("#"))
    return "\n".join(strs)


def main(args) -> None:
    """Main entrypoint. Load available p-isa ops and parse isa instructions."""

    parse_results = Parser().parse_inputs(sys.stdin.readlines())
    Config.legacy_mode = args.legacy

    # String blocks of the p-isa instructions (forward the Nones)
    pisa_ops: list[str | None] = list(
        to_string_block(op, ignore_comments=args.quiet) if op is not None else None
        for op in parse_results.get_pisa_ops()
    )

    filtered = (t for t in zip(pisa_ops, parse_results.commands) if t[0] is not None)

    if args.quiet is True:
        for pisa_op, _ in filtered:
            print(pisa_op)
        return

    hashes = "#" * 3
    context = parse_results.context
    print(hashes, "Context:", context, hashes)
    for kernel_no, (pisa_op, command) in enumerate(filtered):
        print(hashes, f"Kernel ({kernel_no}):", command, hashes)
        print(pisa_op)


if __name__ == "__main__":
    cmdline_args = parse_args()
    main(cmdline_args)
