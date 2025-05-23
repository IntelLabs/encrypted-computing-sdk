#! /usr/bin/env python3
# encoding: utf-8
"""
This module provides functionality for linking assembled kernels into a full HERACLES program for execution queues: MINST, CINST, and XINST.

Classes:
    LinkerRunConfig
        Maintains the configuration data for the run.

    KernelFiles
        Structure for kernel files.

Functions:
    main(run_config: LinkerRunConfig, verbose_stream=None)
        Executes the linking process using the provided configuration.

    parse_args() -> argparse.Namespace
        Parses command-line arguments for the linker script.

Usage:
    This script is intended to be run as a standalone program. It requires specific command-line arguments
    to specify input and output files and configuration options for the linking process.

"""
import argparse
import io
import os
import pathlib
import sys
import time
import warnings

import linker

from typing import NamedTuple

from assembler.common import constants
from assembler.common import makeUniquePath
from assembler.common.counter import Counter
from assembler.common.run_config import RunConfig
from assembler.common.run_config import static_initializer
from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info
from linker import loader
from linker.steps import variable_discovery
from linker.steps import program_linker

@static_initializer
class LinkerRunConfig(RunConfig):
    """
    Maintains the configuration data for the run.

    Methods:
        as_dict() -> dict
            Returns the configuration as a dictionary.
    """

    __initialized = False # specifies whether static members have been initialized
    # contains the dictionary of all configuration items supported and their
    # default value (or None if no default)
    __default_config = {}

    def __init__(self, **kwargs):
        """
        Constructs a new LinkerRunConfig Object from input parameters.

        See base class constructor for more parameters.

        Args:
            input_prefixes (list[str]):
                List of input prefixes, including full path. For an input prefix, linker will
                assume there are three files named `input_prefixes[i] + '.minst'`,
                `input_prefixes[i] + '.cinst'`, and `input_prefixes[i] + '.xinst'`.
                This list must not be empty.
            output_prefix (str):
                Prefix for the output file names.
                Three files will be generated:
                `output_dir/output_prefix.minst`, `output_dir/output_prefix.cinst`, and
                `output_dir/output_prefix.xinst`.
                Output filenames cannot match input file names.
            input_mem_file (str):
                Input memory file associated with the result kernel.
            output_dir (str): current working directory
                OPTIONAL directory where to store all intermediate files and final output.
                This will be created if it doesn't exists.
                Defaults to current working directory.

        Raises:
            TypeError:
                A mandatory configuration value was missing.
            ValueError:
                At least, one of the arguments passed is invalid.
        """

        super().__init__(**kwargs)


        # class members based on configuration
        for config_name, default_value in self.__default_config.items():
            assert(not hasattr(self, config_name))
            setattr(self, config_name, kwargs.get(config_name, default_value))
            if getattr(self, config_name) is None:
                raise TypeError(f'Expected value for configuration `{config_name}`, but `None` received.')

        # fix file names
        self.output_dir = makeUniquePath(self.output_dir)
        self.input_mem_file = makeUniquePath(self.input_mem_file)

    @classmethod
    def init_static(cls):
        """
        Initializes static members of the class.
        """
        if not cls.__initialized:
            cls.__default_config["input_prefixes"]  = None
            cls.__default_config["input_mem_file"]  = None
            cls.__default_config["output_dir"]      = os.getcwd()
            cls.__default_config["output_prefix"]   = None
            cls.__default_config["has_hbm"]         = True

            cls.__initialized = True

    def __str__(self):
        """
        Provides a string representation of the configuration.
    
        Returns:
            str: The string for the configuration.
        """
        self_dict = self.as_dict()
        with io.StringIO() as retval_f:
            for key, value in self_dict.items():
                print("{}: {}".format(key, value), file=retval_f)
            retval = retval_f.getvalue()
        return retval

    def as_dict(self) -> dict:
        """
        Provides the configuration as a dictionary.

        Returns:
            dict: The configuration.
        """
        retval = super().as_dict()
        tmp_self_dict = vars(self)
        retval.update({ config_name: tmp_self_dict[config_name] for config_name in self.__default_config })
        return retval

class KernelFiles(NamedTuple):
    """
    Structure for kernel files.

    Attributes:
        minst (str):
            Index = 0. Name for file containing MInstructions for represented kernel.
        cinst (str):
            Index = 1. Name for file containing CInstructions for represented kernel.
        xinst (str):
            Index = 2. Name for file containing XInstructions for represented kernel.
        prefix (str):
            Index = 3
    """
    minst: str
    cinst: str
    xinst: str
    prefix: str

def main(run_config: LinkerRunConfig, verbose_stream = None):
    """
    Executes the linking process using the provided configuration.

    This function prepares input and output file names, initializes the memory model, discovers variables,
    and links each kernel, writing the output to specified files.

    Args:
        run_config (LinkerRunConfig): The configuration object containing run parameters.
        verbose_stream: The stream to which verbose output is printed. Defaults to None.

    Returns:
        None
    """
    if verbose_stream:
        print("Linking...", file=verbose_stream)

    if run_config.use_xinstfetch:
        warnings.warn(f'Ignoring configuration flag "use_xinstfetch".')

    # Update global config
    GlobalConfig.hasHBM = run_config.has_hbm

    mem_filename: str         = run_config.input_mem_file
    hbm_capcity_words: int    = constants.convertBytes2Words(run_config.hbm_size * constants.Constants.KILOBYTE)
    input_files               = [] # list(KernelFiles)
    output_files: KernelFiles = None

    # prepare output file names
    output_prefix = os.path.join(run_config.output_dir, run_config.output_prefix)
    output_dir = os.path.dirname(output_prefix)
    pathlib.Path(output_dir).mkdir(exist_ok = True, parents=True)
    output_files = KernelFiles(minst=makeUniquePath(output_prefix + '.minst'),
                               cinst=makeUniquePath(output_prefix + '.cinst'),
                               xinst=makeUniquePath(output_prefix + '.xinst'),
                               prefix=makeUniquePath(output_prefix))

    # prepare input file names
    for file_prefix in run_config.input_prefixes:
        input_files.append(KernelFiles(minst=makeUniquePath(file_prefix + '.minst'),
                                       cinst=makeUniquePath(file_prefix + '.cinst'),
                                       xinst=makeUniquePath(file_prefix + '.xinst'),
                                       prefix=makeUniquePath(file_prefix)))
        for input_filename in input_files[-1][:-1]:
            if not os.path.isfile(input_filename):
                raise FileNotFoundError(input_filename)
            if input_filename in output_files:
                raise RuntimeError(f'Input files cannot match output files: "{input_filename}"')

    # reset counters
    Counter.reset()

    # parse mem file

    if verbose_stream:
        print("", file=verbose_stream)
        print("Interpreting variable meta information...", file=verbose_stream)

    with open(mem_filename, 'r') as mem_ifnum:
        mem_meta_info = mem_info.MemInfo.from_iter(mem_ifnum)

    # initialize memory model
    if verbose_stream:
        print("Initializing linker memory model", file=verbose_stream)

    mem_model = linker.MemoryModel(hbm_capcity_words, mem_meta_info)
    if verbose_stream:
        print(f"  HBM capacity: {mem_model.hbm.capacity} words", file=verbose_stream)

    # find all variables and usage across all the input kernels

    if verbose_stream:
        print("  Finding all program variables...", file=verbose_stream)
        print("  Scanning", file=verbose_stream)

    for idx, kernel in enumerate(input_files):
        if not GlobalConfig.hasHBM:
            if verbose_stream:
                print("    {}/{}".format(idx + 1, len(input_files)), kernel.cinst,
                      file=verbose_stream)
            # load next CInst kernel and scan for variables used in SPAD
            kernel_cinstrs = loader.loadCInstKernelFromFile(kernel.cinst)
            for var_name in variable_discovery.discoverVariablesSPAD(kernel_cinstrs):
                mem_model.addVariable(var_name)
        else:
            if verbose_stream:
                print("    {}/{}".format(idx + 1, len(input_files)), kernel.minst,
                    file=verbose_stream)
            # load next MInst kernel and scan for variables used
            kernel_minstrs = loader.loadMInstKernelFromFile(kernel.minst)
            for var_name in variable_discovery.discoverVariables(kernel_minstrs):
                mem_model.addVariable(var_name)

    # check that all non-keygen variables from MemInfo are used
    for var_name in mem_model.mem_info_vars:
        if var_name not in mem_model.variables:
            if GlobalConfig.hasHBM or var_name not in mem_model.mem_info_meta: # skip checking meta vars when no HBM
                raise RuntimeError(f'Unused variable from input mem file: "{var_name}" not in memory model.')

    if verbose_stream:
        print(f"    Variables found: {len(mem_model.variables)}", file=verbose_stream)

    if verbose_stream:
        print("Linking started", file=verbose_stream)

    # open the output files
    with open(output_files.minst, 'w') as fnum_output_minst, \
         open(output_files.cinst, 'w') as fnum_output_cinst, \
         open(output_files.xinst, 'w') as fnum_output_xinst:

        # prepare the linker class
        result_program = program_linker.LinkedProgram(fnum_output_minst,
                                                      fnum_output_cinst,
                                                      fnum_output_xinst,
                                                      mem_model,
                                                      supress_comments=run_config.suppress_comments)
        # start linking each kernel
        for idx, kernel in enumerate(input_files):
            if verbose_stream:
                print("[ {: >3}% ]".format(idx * 100 // len(input_files)), kernel.prefix,
                      file=verbose_stream)
            kernel_minstrs = loader.loadMInstKernelFromFile(kernel.minst)
            kernel_cinstrs = loader.loadCInstKernelFromFile(kernel.cinst)
            kernel_xinstrs = loader.loadXInstKernelFromFile(kernel.xinst)

            result_program.linkKernel(kernel_minstrs, kernel_cinstrs, kernel_xinstrs)

        if verbose_stream:
            print("[ 100% ] Finalizing output", output_files.prefix, file=verbose_stream)

        # signal that we have linked all kernels
        result_program.close()

    if verbose_stream:
        print("Output written to files:", file=verbose_stream)
        print("  ", output_files.minst, file=verbose_stream)
        print("  ", output_files.cinst, file=verbose_stream)
        print("  ", output_files.xinst, file=verbose_stream)

def parse_args():
    """
    Parses command-line arguments for the linker script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("HERACLES Linker.\n"
                     "Links assembled kernels into a full HERACLES program "
                     "for each of the three execution queues: MINST, CINST, and XINST.\n\n"
                     "To link several kernels, specify each kernel's input prefix in order. "
                     "Variables that should carry on across kernels should be have the same name. "
                     "Linker will recognize matching variables and keep their values between kernels. "
                     "Variables that are inputs and outputs (and metadata) for the whole program must "
                     "be indicated in the input memory mapping file."))
    parser.add_argument("input_prefixes", nargs="+",
                        help=("List of input prefixes, including full path. For an input prefix, linker will "
                              "assume three files exist named `input_prefixes[i] + '.minst'`, "
                              "`input_prefixes[i] + '.cinst'`, and `input_prefixes[i] + '.xinst'`."))
    parser.add_argument("-im", "--input_mem_file", dest="input_mem_file", required=True,
                        help=("Input memory mapping file associated with the resulting program. "
                              "Specifies the names for input, output, and metadata variables for the full program. "
                              "This file is usually the same as the kernel's when converting a single kernel into "
                              "a program, but, when linking multiple kernels together, it should be tailored to the "
                              "whole program."))
    parser.add_argument("-o", "--output_prefix", dest="output_prefix", required=True,
                        help=("Prefix for the output file names. "
                              "Three files will be generated: \n"
                              "`output_dir/output_prefix.minst`, `output_dir/output_prefix.cinst`, and "
                              "`output_dir/output_prefix.xinst`. \n"
                              "Output filenames cannot match input file names."))
    parser.add_argument("-od", "--output_dir", dest="output_dir", default="",
                        help=("Directory where to store all intermediate files and final output. "
                              "This will be created if it doesn't exists. "
                              "Defaults to current working directory."))
    parser.add_argument("--hbm_size", type=int, default=LinkerRunConfig.DEFAULT_HBM_SIZE_KB,
                        help="HBM size in KB. Defaults to {} KB.".format(LinkerRunConfig.DEFAULT_HBM_SIZE_KB))
    parser.add_argument("--no_hbm", dest="has_hbm", action="store_false",
                        help="If set, this flag tells he_prep there is no HBM in the target chip.")
    parser.add_argument("--suppress_comments", "--no_comments", dest="suppress_comments", action="store_true",
                        help=("When enabled, no comments will be emited on the output generated."))
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help=("If enabled, extra information and progress reports are printed to stdout. "
                              "Increase level of verbosity by specifying flag multiple times, e.g. -vv"))
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    module_name = os.path.basename(__file__)

    args = parse_args()
    config = LinkerRunConfig(**vars(args)) # convert argsparser into a dictionary

    if args.verbose > 0:
        print(module_name)
        print()
        print("Run Configuration")
        print("=================")
        print(config)
        print("=================")
        print()

    main(config, sys.stdout if args.verbose > 1 else None)

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
