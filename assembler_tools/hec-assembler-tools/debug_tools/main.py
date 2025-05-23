import os
import sys
import time
import argparse

from assembler.common import constants
from assembler.common.config import GlobalConfig
from assembler.instructions import xinst
from assembler.stages import preprocessor
from assembler.stages import scheduler
from assembler.stages.scheduler import schedulePISAInstructions
from assembler.stages.asm_scheduler import scheduleASMISAInstructions
from assembler.memory_model import MemoryModel
from assembler.memory_model import mem_info
from assembler.isa_spec import SpecConfig

def parse_args():
    """
    Parses command-line arguments for the preprocessing script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("Main Test.\n"))
    parser.add_argument("--mem_file", default="", help="Input memory file.")
    parser.add_argument("--prefix", default="", dest="base_names", nargs='+', help="One or more input prefix to process.")
    parser.add_argument("--isa_spec", default="", dest="isa_spec_file",
                        help=("Input ISA specification (.json) file."))
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help=("If enabled, extra information and progress reports are printed to stdout. "
                              "Increase level of verbosity by specifying flag multiple times, e.g. -vv"))
    args = parser.parse_args()

    return args

def main_readmem(args):
    """
    Reads and processes memory information from a file.
    """
    import sys
    import yaml
    import io

    if args.mem_file:
        mem_filename = args.mem_file
    else:
        raise argparse.ArgumentError(None, "Please provide input memory file using `--mem_file` option.")

    mem_meta_info = None
    with open(mem_filename, 'r') as mem_ifnum:
        mem_meta_info = mem_info.MemInfo.from_iter(mem_ifnum)

    if mem_meta_info:
        with io.StringIO() as retval_f:
            yaml.dump(mem_meta_info.as_dict(), retval_f, sort_keys=False)
            yaml_str = retval_f.getvalue()

        print(yaml_str)
        print("--------------")
        new_meminfo = yaml.safe_load(yaml_str)
        print(new_meminfo)
        print("--------------")
        mem_meta_info = mem_info.MemInfo(**new_meminfo)
        yaml.dump(mem_meta_info.as_dict(), sys.stdout, sort_keys=False)
    else:
        print("None")

def asmisa_preprocessing(input_filename: str,
                         output_filename: str,
                         b_use_bank_0: bool,
                         b_verbose=True) -> int:
    """
    Preprocess P-ISA kernel and save the intermediate result.

    Parameters:
        input_filename (str): The input file containing the P-ISA kernel.
        output_filename (str): The output file to save the intermediate result.
        b_use_bank_0 (bool): Whether to use bank 0.
        b_verbose (bool): Whether to print verbose output.

    Returns:
        int: The time taken for preprocessing in seconds.
    """
    if b_verbose:
        print('Preprocessing P-ISA kernel...')

    hec_mem_model = MemoryModel(constants.MemoryModel.HBM.MAX_CAPACITY_WORDS,
                                constants.MemoryModel.SPAD.MAX_CAPACITY_WORDS)

    start_time = time.time()

    with open(input_filename, 'r') as insts:
        insts_listing = preprocessor.preprocessPISAKernelListing(hec_mem_model,
                                                                 insts,
                                                                 progress_verbose=b_verbose)

    if b_verbose:
        print("Assigning register banks to variables...")
    preprocessor.assignRegisterBanksToVars(hec_mem_model, insts_listing, use_bank0=b_use_bank_0)

    retval_timing = time.time() - start_time

    if b_verbose:
        print("Saving intermediate...")
    with open(output_filename, 'w') as outnum:
        for inst in insts_listing:
            inst_line = inst.toPISAFormat()  # + f" # {inst.id}"
            if inst_line:
                print(inst_line, file=outnum)

    return retval_timing

def asmisa_assembly(output_xinst_filename: str,
                    output_cinst_filename: str,
                    output_minst_filename: str,
                    output_mem_filename: str,
                    input_filename: str,
                    mem_filename: str,
                    max_bundle_size: int,
                    hbm_capcity_words: int,
                    spad_capacity_words: int,
                    num_register_banks: int = constants.MemoryModel.NUM_REGISTER_BANKS,
                    register_range: range = None,
                    b_verbose=True) -> tuple:
    """
    Assembles ASM-ISA instructions from preprocessed P-ISA kernel.

    Parameters:
        output_xinst_filename (str): The output file for XInst instructions.
        output_cinst_filename (str): The output file for CInst instructions.
        output_minst_filename (str): The output file for MInst instructions.
        output_mem_filename (str): The output file for memory information.
        input_filename (str): The input file containing the preprocessed P-ISA kernel.
        mem_filename (str): The file containing memory information.
        max_bundle_size (int): Maximum number of instructions in a bundle.
        hbm_capcity_words (int): Capacity of HBM in words.
        spad_capacity_words (int): Capacity of SPAD in words.
        num_register_banks (int): Number of register banks.
        register_range (range): Range of registers.
        b_verbose (bool): Whether to print verbose output.

    Returns:
        tuple: A tuple containing the number of XInsts, NOPs, idle cycles, dependency timing, and scheduling timing.
    """
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
            # Instruction is one that is represented by single XInst
            inst = xinst.createFromPISALine(hec_mem_model, s_line, line_no)
            if inst:
                parsed_insts = [inst]

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
    dep_graph = scheduler.generateInstrDependencyGraph(insts_listing)
    deps_end = time.time() - start_time

    if b_verbose:
        print("Scheduling ASM-ISA instructions...")
    start_time = time.time()
    minsts, cinsts, xinsts, num_idle_cycles = scheduleASMISAInstructions(dep_graph,
                                                                        max_bundle_size,
                                                                        hec_mem_model,
                                                                        constants.Constants.REPLACEMENT_POLICY_FTBU,
                                                                        b_verbose)
    sched_end = time.time() - start_time
    num_nops = 0
    num_xinsts = 0
    for bundle_xinsts, *_ in xinsts:
        for xinstr in bundle_xinsts:
            num_xinsts += 1
            if isinstance(xinstr, xinst.Exit):
                break  # Stop counting instructions after bundle exit
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

    if output_mem_filename:
        if b_verbose:
            print("Saving mem...")
        with open(output_mem_filename, 'w') as outnum:
            mem_meta_info.exportLegacyMem(outnum)

    return num_xinsts, num_nops, num_idle_cycles, deps_end, sched_end

def main_asmisa(args):
    """
    Main function to run ASM-ISA assembly process.
    """
    b_use_bank_0: bool = False
    b_use_old_mem_file = False
    b_verbose = True if args.verbose > 0 else False
    GlobalConfig.debugVerbose = 0
    GlobalConfig.suppressComments = False
    GlobalConfig.useHBMPlaceHolders = True
    GlobalConfig.useXInstFetch = False

    max_bundle_size = constants.Constants.MAX_BUNDLE_SIZE
    hbm_capcity_words = constants.MemoryModel.HBM.MAX_CAPACITY_WORDS // 2
    spad_capacity_words = constants.MemoryModel.SPAD.MAX_CAPACITY_WORDS
    num_register_banks = constants.MemoryModel.NUM_REGISTER_BANKS
    register_range = None

    # All base names for processing
    if len(args.base_names) > 0:
        all_base_names = args.base_names
    else:
        raise argparse.ArgumentError(f"Please provide one or more input file prefixes using `--prefix` option.")

    for base_name in all_base_names:
        in_kernel = f'{base_name}.csv'
        mem_kernel = f'{base_name}.tw.mem'
        mid_kernel = f'{base_name}.tw.csv'
        out_xinst = f'{base_name}.xinst'
        out_cinst = f'{base_name}.cinst'
        out_minst = f'{base_name}.minst'
        out_mem = f'{base_name}.mem' if b_use_old_mem_file else None

        if b_verbose:
            print("Verbose mode: ON")

        print('Input:', in_kernel)

        # Preprocessing
        insts_end = asmisa_preprocessing(in_kernel, mid_kernel, b_use_bank_0, b_verbose)

        if b_verbose:
            print()

        num_xinsts, num_nops, num_idle_cycles, deps_end, sched_end = \
            asmisa_assembly(out_xinst,
                            out_cinst,
                            out_minst,
                            out_mem,
                            mid_kernel,
                            mem_kernel,
                            max_bundle_size,
                            hbm_capcity_words,
                            spad_capacity_words,
                            num_register_banks,
                            register_range,
                            b_verbose=b_verbose)

        if b_verbose:
            print(f"Input: {in_kernel}")
            print(f"Intermediate: {mid_kernel}")
            print(f"--- Preprocessing time: {insts_end} seconds ---")
            print(f"--- Total XInstructions: {num_xinsts} ---")
            print(f"--- Deps time: {deps_end} seconds ---")
            print(f"--- Scheduling time: {sched_end} seconds ---")
            print(f"--- Minimum idle cycles: {num_idle_cycles} ---")
            print(f"--- Minimum nops required: {num_nops} ---")
            print()

    print("Complete")

def main_pisa(args):
    """
    Main function to run P-ISA scheduling process.
    """
    b_use_bank_0: bool = False
    b_verbose = True if args.verbose > 0 else False

    max_bundle_size = 8
    hec_mem_model = MemoryModel(constants.MemoryModel.HBM.MAX_CAPACITY_WORDS // 2,
                                16,
                                4,
                                range(8))
    
    if len(args.base_names) == 1:
        base_name = args.base_names[0]
    else:
        raise argparse.ArgumentError(None, f"Please provide an input file prefix using `--prefix` option.")
    
    print("HBM")
    print(hec_mem_model.hbm.CAPACITY / constants.Constants.GIGABYTE, "GB")
    print(hec_mem_model.hbm.CAPACITY_WORDS, "words")
    print()


    in_kernel = f'{base_name}.csv'
    mid_kernel = f'{base_name}.tw.csv'
    out_kernel = f'{base_name}.tw.new.csv'
    out_xinst = f'{base_name}.xinst'
    out_cinst = f'{base_name}.cinst'
    out_minst = f'{base_name}.minst'

    insts_listing = []
    start_time = time.time()
    # Read input kernel and pre-process P-ISA:
    # Resulting instructions will be correctly transformed and ready to be converted into ASM-ISA instructions;
    # Variables used in the kernel will be automatically assigned to banks.
    with open(in_kernel, 'r') as insts:
        insts_listing = preprocessor.preprocessPISAKernelListing(hec_mem_model,
                                                                 insts,
                                                                 progress_verbose=b_verbose)

    print("Assigning register banks to variables...")
    preprocessor.assignRegisterBanksToVars(hec_mem_model, insts_listing, use_bank0=b_use_bank_0)

    hec_mem_model.output_variables.update(v_name for v_name in hec_mem_model.variables if 'output' in v_name)

    insts_end = time.time() - start_time

    print("Saving intermediate...")
    with open(mid_kernel, 'w') as outnum:
        for inst in insts_listing:
            inst_line = inst.toPISAFormat() + f" # {inst.id}"
            if inst_line:
                print(inst_line, file=outnum)

    #print("Reloading kernel from intermediate...")
    #insts_listing = []
    #with open(mid_kernel, 'r') as insts:
    #    for line_no, s_line in enumerate(insts, 1):
    #        parsed_insts = None
    #        if line_no % 100 == 0:
    #            print(f"{line_no}")
    #        # instruction is one that is represented by single XInst
    #        inst = xinst.createFromPISALine(hec_mem_model, s_line, line_no)
    #        if inst:
    #            parsed_insts = [ inst ]

    #        if not parsed_insts:
    #            raise SyntaxError("Line {}: unable to parse kernel instruction:\n{}".format(line_no, s_line))

    #        insts_listing += parsed_insts

    print("Generating dependency graph...")
    start_time = time.time()
    dep_graph = preprocessor.generateInstrDependencyGraph(insts_listing)
    deps_end = time.time() - start_time

    # Assign artificial register to allow scheduling of P-ISA
    for v in hec_mem_model.variables.values():
        v.register = hec_mem_model.register_banks[0].getRegister(0)

    print("Scheduling P-ISA instructions...")
    start_time = time.time()
    pisa_insts_schedule, num_idle_cycles, num_nops = schedulePISAInstructions(dep_graph, progress_verbose=b_verbose)
    sched_end = time.time() - start_time

    print("Saving...")
    with open(out_kernel, 'w') as outnum:
        for idx, inst in enumerate(pisa_insts_schedule):
            inst_line = inst.toPISAFormat()
            if inst_line:
                print(inst_line, file=outnum)

    print(f"Input: {in_kernel}")
    print(f"Intermediate: {mid_kernel}")
    print(f"Output: {out_kernel}")
    print(f"Instructions generated: {len(insts_listing)}")
    print(f"--- Generation time: {insts_end} seconds ---")
    print(f"--- Number of instructions: {len(insts_listing)} ---")
    print(f"--- Deps time: {deps_end} seconds ---")
    print(f"--- Scheduling time: {sched_end} seconds ---")
    print(f"--- Minimum idle cycles: {num_idle_cycles} ---")
    print(f"--- Minimum nops required: {num_nops} ---")

    print("Complete")

if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)

    sys.path.append(os.path.join(module_dir,'xinst_timing_check'))
    print(module_dir,'xinst_timing_check')
    args = parse_args()

    repo_dir = os.path.join(module_dir,"..")
    args.isa_spec_file = SpecConfig.initialize_isa_spec(repo_dir, args.isa_spec_file)
    if args.verbose > 0:
        print(f"ISA Spec: {args.isa_spec_file}")

    main_asmisa(args)
