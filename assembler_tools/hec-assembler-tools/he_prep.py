#! /usr/bin/env python3

"""
This module provides functionality for preprocessing P-ISA abstract kernels before further assembling for HERACLES.

Functions:
    __savePISAListing(out_stream, instr_listing: list)
        Stores instructions to a stream in P-ISA format.

    main(output_file_name: str, input_file_name: str, b_verbose: bool)
        Preprocesses the P-ISA kernel and saves the output to a specified file.

    parse_args() -> argparse.Namespace
        Parses command-line arguments for the preprocessing script.

Usage:
    This script is intended to be run as a standalone program. It requires specific command-line arguments
    to specify input and output files and verbosity options for the preprocessing process.

"""
import argparse
import os
import time

from assembler.common import constants
from assembler.isa_spec import SpecConfig
from assembler.stages import preprocessor
from assembler.memory_model import MemoryModel

def __savePISAListing(out_stream,
                      instr_listing: list):
    """
    Stores the instructions to a stream in P-ISA format.

    This function iterates over a list of instructions and prints each instruction in P-ISA format
    to the specified output stream.

    Args:
        out_stream: The output stream to which the instructions are printed.
        instr_listing (list): A list of instructions to be printed in P-ISA format.

    Returns:
        None
    """
    for inst in instr_listing:
        inst_line = inst.toPISAFormat()
        if inst_line:
            print(inst_line, file=out_stream)

def main(output_file_name: str,
         input_file_name: str,
         b_verbose: bool):
    """
    Preprocesses the P-ISA kernel and saves the output to a specified file.

    This function reads an input kernel file, preprocesses it to transform instructions into ASM-ISA format,
    assigns register banks to variables, and saves the processed instructions to an output file.

    Args:
        output_file_name (str): The name of the output file where processed instructions are saved.
        input_file_name (str): The name of the input file containing the P-ISA kernel.
        b_verbose (bool): Flag indicating whether verbose output is enabled.

    Returns:
        None
    """
    # used for timings
    insts_end: int = 0

    # check for default `output_file_name`
    # e.g. of default
    #   input_file_name = /path/to/some/file.csv
    #   output_file_name = /path/to/some/file.tw.csv
    if not output_file_name:
        output_file_name = os.path.splitext(input_file_name)
        output_file_name = ''.join(output_file_name[:-1] + (".tw",) + output_file_name[-1:])

    hec_mem_model = MemoryModel(constants.MemoryModel.HBM.MAX_CAPACITY_WORDS,
                                constants.MemoryModel.SPAD.MAX_CAPACITY_WORDS)

    insts_listing = []
    start_time = time.time()
    # read input kernel and pre-process P-ISA:
    # resulting instructions will be correctly transformed and ready to be converted into ASM-ISA instructions;
    # variables used in the kernel will be automatically assigned to banks.
    with open(input_file_name, 'r') as insts:
        insts_listing = preprocessor.preprocessPISAKernelListing(hec_mem_model,
                                                                 insts,
                                                                 progress_verbose=b_verbose)
    num_input_instr: int = len(insts_listing) # track number of instructions in input kernel
    if b_verbose:
        print("Assigning register banks to variables...")
    preprocessor.assignRegisterBanksToVars(hec_mem_model,
                                           insts_listing,
                                           use_bank0=False,
                                           verbose=b_verbose)
    insts_end = time.time() - start_time

    if b_verbose:
        print("Saving...")
    with open(output_file_name, 'w') as outnum:
        __savePISAListing(outnum, insts_listing)

    if b_verbose:
        print(f"Input: {input_file_name}")
        print(f"Output: {output_file_name}")
        print(f"Instructions in input: {num_input_instr}")
        print(f"Instructions in output: {len(insts_listing)}")
        print(f"--- Generation time: {insts_end} seconds ---")

def parse_args():
    """
    Parses command-line arguments for the preprocessing script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="HERACLES Assembling Pre-processor.\nThis program performs the preprocessing of P-ISA abstract kernels before further assembling.")
    parser.add_argument("input_file_name", help="Input abstract kernel file to which to add twiddle factors.")
    parser.add_argument("output_file_name", nargs="?", help="Output file name. Defaults to <input_file_name_no_ext>.tw.<input_file_name_ext>")
    parser.add_argument("--isa_spec", default="", dest="isa_spec_file",
                        help=("Input ISA specification (.json) file."))
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help=("If enabled, extra information and progress reports are printed to stdout. "
                              "Increase level of verbosity by specifying flag multiple times, e.g. -vv"))
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)

    args = parse_args()

    args.isa_spec_file = SpecConfig.initialize_isa_spec(module_dir, args.isa_spec_file)

    if args.verbose > 0:
        print(module_name)
        print()
        print("Input: {0}".format(args.input_file_name))
        print("Output: {0}".format(args.output_file_name))
        print("ISA Spec: {0}".format(args.isa_spec_file))

    main(output_file_name=args.output_file_name,
         input_file_name=args.input_file_name,
         b_verbose=(args.verbose > 1))

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
