#! /usr/bin/env python3
"""
This module provides functionality for assembling pre-processed P-ISA kernel programs into valid assembly code for execution queues: MINST, CINST, and XINST.

Classes:
    AssemblerRunConfig
        Maintains the configuration data for the run.

Functions:
    asmisaAssemble(run_config, output_minst_filename: str, output_cinst_filename: str, output_xinst_filename: str, b_verbose=True) -> tuple
        Assembles the P-ISA kernel into ASM-ISA instructions and saves them to specified output files.

    main(config: AssemblerRunConfig, verbose: bool = False)
        Executes the assembly process using the provided configuration.

    parse_args() -> argparse.Namespace
        Parses command-line arguments for the assembler script.

Usage:
    This script is intended to be run as a standalone program. It requires specific command-line arguments
    to specify input and output files and configuration options for the assembly process.

"""
import argparse
import io
import os
import pathlib
import sys
import time

from assembler.common.run_config import RunConfig
from assembler.common.run_config import static_initializer

from assembler.common import constants
from assembler.common import makeUniquePath
from assembler.common.config import GlobalConfig
from assembler.common.counter import Counter
from assembler.isa_spec import SpecConfig
from assembler.instructions import xinst
from assembler.stages import scheduler
from assembler.stages.asm_scheduler import scheduleASMISAInstructions
from assembler.memory_model import MemoryModel
from assembler.memory_model import mem_info

script_dir = os.path.dirname(os.path.realpath(__file__))

# module constants
DEFAULT_XINST_FILE_EXT = "xinst"
DEFAULT_CINST_FILE_EXT = "cinst"
DEFAULT_MINST_FILE_EXT = "minst"
DEFAULT_MEM_FILE_EXT = "mem"

@static_initializer
class AssemblerRunConfig(RunConfig):
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
        Constructs a new AssemblerRunConfig Object from input parameters.

        See base class constructor for more parameters.

        Args:
            input_file (str):
                Input file containing the kernel code to assemble.
                Kernel code should have twiddle factors added already as appropriate.
            input_mem_file (str):
                Optional input memory file associated with the kernel.
                If missing, the memory file is expected to be same as `input_file`, but with extension ".mem".
            output_dir (str):
                Optional directory where to store all intermediate files and final output.
                This will be created if it doesn't exists.
                Defaults to the same directory as the input file.
            output_prefix (str):
                Optional prefix for the output file names.
                Defaults to the name of the input file without extension.

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

        # class members
        self.input_prefix = ""

        # fix file names

        self.input_file = makeUniquePath(self.input_file)
        input_dir = os.path.dirname(os.path.realpath(self.input_file))
        if not self.output_dir:
            self.output_dir = input_dir
        self.output_dir = makeUniquePath(self.output_dir)

        self.input_prefix = os.path.splitext(os.path.basename(self.input_file))[0]

        if not self.input_mem_file:
            self.input_mem_file = "{}.{}".format(os.path.join(input_dir, self.input_prefix),
                                                 DEFAULT_MEM_FILE_EXT)
        self.input_mem_file = makeUniquePath(self.input_mem_file)

    @classmethod
    def init_static(cls):
        """
        Initializes static members of the class.
        """
        if not cls.__initialized:
            cls.__default_config["input_file"]      = None
            cls.__default_config["input_mem_file"]  = ""
            cls.__default_config["output_dir"]      = ""
            cls.__default_config["output_prefix"]   = ""
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

def asmisaAssemble(run_config,
                   output_minst_filename: str,
                   output_cinst_filename: str,
                   output_xinst_filename: str,
                   b_verbose=True) -> tuple:
    """
    Assembles the P-ISA kernel into ASM-ISA instructions and saves them to specified output files.

    This function reads the input kernel file, interprets variable meta information, generates a dependency graph,
    schedules ASM-ISA instructions, and saves the results to output files.

    Args:
        run_config: The configuration object containing run parameters.
        output_minst_filename (str): The filename for saving MINST instructions.
        output_cinst_filename (str): The filename for saving CINST instructions.
        output_xinst_filename (str): The filename for saving XINST instructions.
        b_verbose (bool): Flag indicating whether verbose output is enabled.

    Returns:
        tuple: A tuple containing the number of XInstructions, number of NOPs, number of idle cycles, dependency timing, and scheduling timing.
    """

    max_bundle_size = 64

    input_filename: str         = run_config.input_file
    mem_filename: str           = run_config.input_mem_file
    hbm_capcity_words: int      = constants.convertBytes2Words(run_config.hbm_size * constants.Constants.KILOBYTE)
    spad_capacity_words: int    = constants.convertBytes2Words(run_config.spad_size * constants.Constants.KILOBYTE)
    num_register_banks: int     = constants.MemoryModel.NUM_REGISTER_BANKS
    register_range: range       = None

    if b_verbose:
        print("Assembling!")
        print("Reloading kernel from intermediate...")

    hec_mem_model = MemoryModel(hbm_capcity_words, spad_capacity_words, num_register_banks, register_range)

    insts_listing = []
    with open(input_filename, 'r') as insts:
        for line_no, s_line in enumerate(insts, 1):
            parsed_insts = None
            if GlobalConfig.debugVerbose:
                if line_no % 100 == 0:
                    print(f"{line_no}")
            # instruction is one that is represented by single XInst
            inst = xinst.createFromPISALine(hec_mem_model, s_line, line_no)
            if inst:
                parsed_insts = [ inst ]

            if not parsed_insts:
                raise SyntaxError("Line {}: unable to parse kernel instruction:\n{}".format(line_no, s_line))

            insts_listing += parsed_insts

    if b_verbose:
        print("Interpreting variable meta information...")
    with open(mem_filename, 'r') as mem_ifnum:
        mem_meta_info = mem_info.MemInfo.from_iter(mem_ifnum)
    mem_info.updateMemoryModelWithMemInfo(hec_mem_model, mem_meta_info)

    if b_verbose:
        print("Generating dependency graph...")
    start_time = time.time()
    dep_graph = scheduler.generateInstrDependencyGraph(insts_listing,
                                                       sys.stdout if b_verbose else None)
    scheduler.enforceKeygenOrdering(dep_graph, hec_mem_model, sys.stdout if b_verbose else None)
    deps_end = time.time() - start_time

    if b_verbose:
        print("Preparing to schedule ASM-ISA instructions...")
    start_time = time.time()
    minsts, cinsts, xinsts, num_idle_cycles = scheduleASMISAInstructions(dep_graph,
                                                                         max_bundle_size, # max number of instructions in a bundle
                                                                         hec_mem_model,
                                                                         run_config.repl_policy,
                                                                         b_verbose)
    sched_end = time.time() - start_time
    num_nops = 0
    num_xinsts = 0
    for bundle_xinsts, *_ in xinsts:
        for xinstr in bundle_xinsts:
            num_xinsts += 1
            if isinstance(xinstr, xinst.Exit):
                break # stop counting instructions after bundle exit
            if isinstance(xinstr, xinst.Nop):
                num_nops += 1

    if b_verbose:
        print("Saving minst...")
    with open(output_minst_filename, 'w') as outnum:
        for idx, inst in enumerate(minsts):
            inst_line = inst.toMASMISAFormat()
            if inst_line:
                print(f"{idx}, {inst_line}", file=outnum)

    if b_verbose:
        print("Saving cinst...")
    with open(output_cinst_filename, 'w') as outnum:
        for idx, inst in enumerate(cinsts):
            inst_line = inst.toCASMISAFormat()
            if inst_line:
                print(f"{idx}, {inst_line}", file=outnum)

    if b_verbose:
        print("Saving xinst...")
    with open(output_xinst_filename, 'w') as outnum:
        for bundle_i, bundle_data in enumerate(xinsts):
            for inst in bundle_data[0]:
                inst_line = inst.toXASMISAFormat()
                if inst_line:
                    print(f"F{bundle_i}, {inst_line}", file=outnum)

    return num_xinsts, num_nops, num_idle_cycles, deps_end, sched_end

def main(config: AssemblerRunConfig, verbose: bool = False):
    """
    Executes the assembly process using the provided configuration.

    This function sets up the output directory, initializes output filenames, tests output writability,
    and performs the assembly process, printing results if verbose output is enabled.

    Args:
        config (AssemblerRunConfig): The configuration object containing run parameters.
        verbose (bool): Flag indicating whether verbose output is enabled.

    Returns:
        None
    """
    # check defaults

    # make a copy to avoid changing original config
    config = AssemblerRunConfig(**config.as_dict())

    # create output directory to store outputs (if it doesn't already exist)
    pathlib.Path(config.output_dir).mkdir(exist_ok = True, parents=True)

    # initialize output filenames

    output_basef = os.path.join(config.output_dir, config.output_prefix) \
                   if config.output_prefix \
                   else os.path.join(config.output_dir, config.input_prefix)

    output_xinst_file = f'{output_basef}.{DEFAULT_XINST_FILE_EXT}'
    output_cinst_file = f'{output_basef}.{DEFAULT_CINST_FILE_EXT}'
    output_minst_file = f'{output_basef}.{DEFAULT_MINST_FILE_EXT}'

    # test output is writable
    for filename in (output_minst_file, output_cinst_file, output_xinst_file):
        try:
            with open(filename, 'w') as outnum:
                print("", file=outnum)
        except Exception as ex:
            raise Exception(f'Failed to write to output location "{filename}"') from ex

    GlobalConfig.useHBMPlaceHolders = True #config.use_hbm_placeholders
    GlobalConfig.useXInstFetch = config.use_xinstfetch
    GlobalConfig.supressComments = config.suppress_comments
    GlobalConfig.hasHBM = config.has_hbm
    GlobalConfig.debugVerbose = config.debug_verbose

    Counter.reset()

    num_xinsts, num_nops, num_idle_cycles, deps_end, sched_end = \
        asmisaAssemble(config,
                       output_minst_file,
                       output_cinst_file,
                       output_xinst_file,
                       b_verbose=verbose)

    if verbose:
        print(f"Output:")
        for filename in (output_minst_file, output_cinst_file, output_xinst_file):
            print(f"  {filename}")
        print(f"--- Total XInstructions: {num_xinsts} ---")
        print(f"--- Deps time: {deps_end} seconds ---")
        print(f"--- Scheduling time: {sched_end} seconds ---")
        print(f"--- Minimum idle cycles: {num_idle_cycles} ---")
        print(f"--- Minimum nops required: {num_nops} ---")

def parse_args():
    """
    Parses command-line arguments for the assembler script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("HERACLES Assembler.\n"
                     "The assembler takes a pre-processed P-ISA kernel program and generates "
                     "valid assembly code for each of the three execution queues: MINST, CINST, and XINST."))
    parser.add_argument("input_file",
                        help=("Input pre-processed P-ISA kernel file. "
                              "File must be the result of pre-processing a P-ISA kernel with he_prep.py"))
    parser.add_argument("--isa_spec", default="", dest="isa_spec_file",
                        help=("Input ISA specification (.json) file."))
    parser.add_argument("--input_mem_file", default="", help=("Input memory mapping file associated with the kernel. "
                                                              "Defaults to the same name as the input file, but with `.mem` extension."))
    parser.add_argument("--output_dir", default="", help=("Directory where to store all intermediate files and final output. "
                                              "This will be created if it doesn't exists. "
                                              "Defaults to the same directory as the input file."))
    parser.add_argument("--output_prefix", default="", help=("Prefix for the output files. "
                                                 "Defaults to the same the input file without extension."))
    parser.add_argument("--spad_size", type=int, default=AssemblerRunConfig.DEFAULT_SPAD_SIZE_KB,
                        help="Scratchpad size in KB. Defaults to {} KB.".format(AssemblerRunConfig.DEFAULT_SPAD_SIZE_KB))
    parser.add_argument("--hbm_size", type=int, default=AssemblerRunConfig.DEFAULT_HBM_SIZE_KB,
                        help="HBM size in KB. Defaults to {} KB.".format(AssemblerRunConfig.DEFAULT_HBM_SIZE_KB))
    parser.add_argument("--no_hbm", dest="has_hbm", action="store_false",
                        help="If set, this flag tells he_prep there is no HBM in the target chip.")
    parser.add_argument("--repl_policy", default=AssemblerRunConfig.DEFAULT_REPL_POLICY,
                        choices=constants.Constants.REPLACEMENT_POLICIES,
                        help="Replacement policy for cache evictions. Defaults to {}.".format(AssemblerRunConfig.DEFAULT_REPL_POLICY))
    parser.add_argument("--use_xinstfetch", dest="use_xinstfetch", action="store_true",
                        help=("When enabled, `xinstfetch` instructions are generated in the CInstQ."))
    parser.add_argument("--suppress_comments", "--no_comments", dest="suppress_comments", action="store_true",
                        help=("When enabled, no comments will be emited on the output generated by the assembler."))
    parser.add_argument("--debug_verbose", type=int, default=0)
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

    config = AssemblerRunConfig(**vars(args)) # convert argsparser into a dictionary

    if args.verbose > 0:
        print(module_name)
        print()
        print("Run Configuration")
        print("=================")
        print(config)
        print("=================")
        print()

    main(config, verbose = args.verbose > 1)

    if args.verbose > 0:
        print()
        print(module_name, "- Complete")
