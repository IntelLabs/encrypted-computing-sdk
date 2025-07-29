# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions.
"""Test the expected behaviour of the kerngen script"""

import pathlib
import subprocess
import sys

import pytest

KERNGEN_PATH = pathlib.Path(__file__).parent.parent / "kerngen.py"
KERNGRAPH_PATH = pathlib.Path(__file__).parent.parent / "kerngraph.py"
KERNEL_EXAMPLES_PATH = pathlib.Path(__file__).parent / "kernel_examples"


@pytest.mark.parametrize(
    "input_file,output_file",
    [
        (
            "relin_kernel/input.bgv.16k_l2_m3.relin",
            "relin_kernel/output.bgv.16k_l2_m3.relin",
        ),
        (
            "relin_kernel/input.bgv.16k_l2_m4.relin",
            "relin_kernel/output.bgv.16k_l2_m4.relin",
        ),
    ],
)
def test_kerngen_relin_regression(input_file, output_file):
    """Test kerngen.py with known good kernel input and output files.

    Args:
        input_file: Path to input file relative to kernel_examples directory
        output_file: Path to output file relative to kernel_examples directory
    """

    # Construct full paths
    input_path = KERNEL_EXAMPLES_PATH / input_file
    output_path = KERNEL_EXAMPLES_PATH / output_file

    # Read the input file
    input_content = input_path.read_text().strip()

    # Read the expected output file
    expected_output = output_path.read_text().strip()

    # Run kerngen.py with -q flag (quiet mode)
    result = subprocess.run(
        [sys.executable, str(KERNGEN_PATH), "-q"],
        input=input_content.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    # Get actual output and normalize line endings
    actual_output = result.stdout.decode().strip().replace("\r\n", "\n")
    expected_output = expected_output.replace("\r\n", "\n")

    # Compare the outputs
    assert actual_output == expected_output, (
        f"Kerngen output did not match expected output for {input_file}.\n\n"
        f"Input file: {input_file}\n"
        f"Output file: {output_file}\n\n"
        f"Input content:\n{input_content}\n\n"
        f"Expected output lines: {len(expected_output.splitlines())}\n"
        f"Actual output lines: {len(actual_output.splitlines())}\n\n"
        f"First 5 lines of expected:\n"
        f"{''.join(expected_output.splitlines()[:5])}\n\n"
        f"First 5 lines of actual:\n"
        f"{''.join(actual_output.splitlines()[:5])}\n"
    )


@pytest.mark.parametrize(
    "input_file,output_file",
    [
        (
            "relin_kernel/input.bgv.16k_l2_m3.relin",
            "relin_kernel/output.bgv.16k_l2_m3_p-rns_s-part.relin",
        ),
        (
            "relin_kernel/input.bgv.16k_l2_m4.relin",
            "relin_kernel/output.bgv.16k_l2_m4_p-rns_s-part.relin",
        ),
    ],
)
def test_kerngraph_relin_regression(input_file, output_file):
    """Test kerngraph.py with known good kernel input and output files.

    Uses the pipeline: input -> kerngen.py -l -> kerngraph.py -l -t relin -p rns -s part

    Args:
        input_file: Path to input file relative to kernel_examples directory
        output_file: Path to output file relative to kernel_examples directory
    """

    # Construct full paths
    input_path = KERNEL_EXAMPLES_PATH / input_file
    output_path = KERNEL_EXAMPLES_PATH / output_file

    # Read the input file
    input_content = input_path.read_text().strip()

    # Read the expected output file
    expected_output = output_path.read_text().strip()

    # Step 1: Run kerngen.py with -l flag (legacy mode)
    kerngen_result = subprocess.run(
        [sys.executable, str(KERNGEN_PATH), "-l"],
        input=input_content.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    # Step 2: Run kerngraph.py with kerngen output as input
    kerngraph_result = subprocess.run(
        [
            sys.executable,
            str(KERNGRAPH_PATH),
            "-l",
            "-t",
            "relin",
            "-p",
            "rns",
            "-s",
            "part",
        ],
        input=kerngen_result.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    # Get actual output and normalize line endings
    actual_output = kerngraph_result.stdout.decode().strip().replace("\r\n", "\n")
    expected_output = expected_output.replace("\r\n", "\n")

    # Compare the outputs
    assert actual_output == expected_output, (
        f"Kerngraph output did not match expected output for {input_file}.\n\n"
        f"Input file: {input_file}\n"
        f"Output file: {output_file}\n\n"
        f"Input content:\n{input_content}\n\n"
        f"Expected output lines: {len(expected_output.splitlines())}\n"
        f"Actual output lines: {len(actual_output.splitlines())}\n\n"
        f"First 5 lines of expected:\n"
        f"{''.join(expected_output.splitlines()[:5])}\n\n"
        f"First 5 lines of actual:\n"
        f"{''.join(actual_output.splitlines()[:5])}\n"
    )
