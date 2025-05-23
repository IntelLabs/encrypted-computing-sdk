import argparse
import os
import re

# Given a variable in P-ISA, this script will replace all instructions that do not
# affect the variable with appropriate NOPs.


def parse_args():
    """
    Parses command-line arguments for the preprocessing script.

    This function sets up the argument parser and defines the expected arguments for the script.
    It returns a Namespace object containing the parsed arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=("Isolation Test.\n"
                     "Given a set of variables in P-ISA, this script will replace all instructions that do not"
                     " affect the variable with appropriate NOPs."))
    parser.add_argument("--pisa_file", required= True, help="Input P-ISA prep (.csv) file.")
    parser.add_argument("--xinst_file", required=True, help="Input (xinst) instruction file.")
    parser.add_argument("--out_file", default="", help="Output file name.")
    parser.add_argument("--track", default="", dest="variables_set", nargs='+', help="Set of variables to track.")
    parser.add_argument("-v", "--verbose", dest="verbose", action="count", default=0,
                        help=("If enabled, extra information and progress reports are printed to stdout. "
                              "Increase level of verbosity by specifying flag multiple times, e.g. -vv"))
    args = parser.parse_args()

    return args

if __name__ == "__main__":
    module_name = os.path.basename(__file__)

    args = parse_args()

    # File paths for input and output
    pisa_prep_file = args.pisa_file
    xinst_file = args.xinst_file
    output_file = ""
    if (args.out_file):
        output_file = args.out_file
    else:
        # Create the new file name
        name, ext = os.path.splitext(xinst_file)
        output_file = f"{name}.out{ext}"

    # Set of variables to track
    variables_set = args.variables_set

    if args.verbose > 0:
        print(module_name)
        print()
        print("P-ISA: {0}".format(pisa_prep_file))
        print("Xinst File: {0}".format(xinst_file))
        print("Output Name: {0}".format(output_file))
        print("Tracking: {0}".format(variables_set))

    # Find all related variables
    pisa_instrs = []
    pisa_file_contents = []
    with open(pisa_prep_file, 'r') as f_in_pisa:
        pisa_file_contents = [line for line in f_in_pisa if line]

    l = []
    set_updated = True
    while set_updated:
        set_updated = False
        for line_idx, line in enumerate(pisa_file_contents):
            # Remove comment
            s_split = line.split("#")
            line = s_split[0]
            # Split into components
            tmp_split = map(lambda s: s.strip(), line.split(","))
            s_split = []
            for component in tmp_split:
                s_split.append(component.split('(')[0].strip())
            pisa_instrs.append(s_split[1:])
            if any(x in s_split for x in variables_set):
                # Add all other variables as dependents
                if s_split[1] == 'muli' or s_split[1] == 'maci':
                    s_split = s_split[2:-2]
                else:
                    s_split = s_split[2:-1]
                new_vars = set(v for v in s_split if re.search('^[A-Za-z_][A-Za-z0-9_]*', v))
                if 'iN' in new_vars:
                    print('iN')
                if new_vars - variables_set:
                    l += [x for x in new_vars if x not in variables_set]
                    variables_set |= new_vars
                    set_updated = True

    print(variables_set)

    pisa_instr_num_set = set()
    for idx, s_split in enumerate(pisa_instrs):
        if any(x in s_split for x in variables_set):
            # Variable found in instruction: keep it
            pisa_instr_num_set.add(idx + 1)

    # Keep only xinsts that are used for the kept p-isa instr
    with open(xinst_file, 'r') as f_in:
        with open(output_file, 'w') as f_out:
            for line in f_in:
                # Remove comment
                s_split = line.split("#")
                s_line = s_split[0].strip()
                # Split into components
                s_split = list(map(lambda s: s.strip(), line.split(",")))
                out_line = ''
                if int(s_split[1]) in pisa_instr_num_set:
                    # Xinstruction is needed to complete p-isa instr
                    if s_split[2] not in ('move', 'xstore', 'nop'):
                        out_line = s_line + " # " + str(pisa_instrs[int(s_split[1]) - 1])
                    else:
                        out_line = line.strip()
                elif 'xstore' in s_line:
                    # All xstores are required because they are sync points with CInstQ
                    out_line = s_line.strip()
                elif 'exit' in s_line:
                    # Keep all exits
                    out_line = s_line.strip()
                elif 'rshuffle' in s_line:
                    # Other rshuffles are converted to nops for timing
                    out_line = '{}, {}, nop, {} # rshuffle'.format(s_split[0], s_split[1], s_split[7])
                elif 'nop' in s_line:
                    # Keep nops timing
                    out_line = s_line.strip()
                if not out_line:
                    # Any other instructions are converted to single cycle nop
                    out_line = '{}, {}, nop, 0'.format(s_split[0], s_split[1])
                print(out_line, file=f_out)

    print("Done")
