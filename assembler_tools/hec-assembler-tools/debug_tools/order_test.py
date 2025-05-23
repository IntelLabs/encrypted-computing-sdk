import argparse
import re
import os

# Tests all registers in an XInstQ for whether a register is used out of order based on P-ISA instruction order.
# This only works for kernels without evictions.
def parse_args():
    """
    Parses command-line arguments for the preprocessing script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("Order Test.\n"
                     "Tests all registers in an XInstQ for whether a register is used out of order based on P-ISA instruction order.\n"
                     "This only works for kernels without evictions."))
    parser.add_argument("--input_file", required= True, help="Input (.xinst) file.")
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help=("If enabled, extra information and progress reports are printed to stdout. "
                              "Increase level of verbosity by specifying flag multiple times, e.g. -vv"))
    args = parser.parse_args()

    return args

def convertRegNameToTuple(reg_name) -> tuple:
    """
    Converts a register name to a tuple representation.

    Parameters:
        reg_name (str): The register name in the format 'r<reg>b<bank>'.

    Returns:
        tuple: A tuple containing the bank and register as integers.
    """
    tmp_s = reg_name.split("r")[1]
    tmp_s = tmp_s.split("b")
    return (int(tmp_s[1]), int(tmp_s[0]))

if __name__ == "__main__":
    module_name = os.path.basename(__file__)

    args = parse_args()
    input_file = args.input_file

    if args.verbose > 0:
        print(module_name)
        print()
        print("Xinst File: {0}".format(input_file))
        print()
        print("Starting")

    register_map = {}

    my_rx = "r[0-9]+b[0-3]"
    prev_pisa_inst = 0
    instr_counter = 0
    with open(input_file, 'r') as f_in:
        for line_idx, s_line in enumerate(f_in):
            instr_regs = set()
            s_split = s_line.split("#")
            s_split = s_split[0].split(",")
            pisa_instr_num = int(s_split[1])
            for s in s_split:
                match = re.search(my_rx, s)
                if match:
                    reg_name = s[match.start():match.end()]
                    if reg_name not in instr_regs:
                        instr_regs.add(reg_name)
                        reg = convertRegNameToTuple(reg_name)
                        if reg not in register_map:
                            register_map[reg] = []
                        register_map[reg].append(pisa_instr_num)

    sorted_keys = [x for x in register_map]
    sorted_keys.sort()
    error_map = set()

    for reg in sorted_keys:
        reg_name = f'r{reg[1]}b{reg[0]}'
        print(reg_name, register_map[reg])
        reg_lst = register_map[reg]
        inverted_map = {}
        prev_in = 0
        for idx in range(len(reg_lst)):
            if reg_lst[idx] >= prev_in:
                prev_in = reg_lst[idx]
            else:
                inverted_map[idx] = (prev_in, reg_lst[idx])
        if inverted_map:
            print('*** Ahead:', inverted_map)
            error_map.add(reg_name)

    if error_map:
        raise RuntimeError(f'Registers used out of order: {error_map}')

    print("Done")