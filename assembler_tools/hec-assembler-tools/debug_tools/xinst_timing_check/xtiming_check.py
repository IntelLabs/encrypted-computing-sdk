import argparse
import os

import xinst
from spec_config import XTC_SpecConfig

# Checks timing for register access.
# - Checks if a register is being read from before its write completes.
# - Checks if rshuffles are within correct timing of each other.
# - Checks for bank write conflicts between rshuffles and other instructions.

NUM_BUNDLE_INSTRUCTIONS = 64

def makeUniquePath(path: str):
    """
    Normalizes and expand a given file path.

    Parameters:
        path (str): The file path to normalize and expand.

    Returns:
        str: The normalized and expanded file path.
    """
    return os.path.normcase(os.path.realpath(os.path.expanduser(path)))

def computeXBundleLatency(xinstr_bundle: list) -> int:
    """
    Computes the latency of a bundle of XInstructions.

    Parameters:
        xinstr_bundle (list): A list of XInstructions in a bundle.

    Returns:
        int: The computed latency of the bundle.

    Raises:
        RuntimeError: If the bundle size is invalid.
    """
    if len(xinstr_bundle) != NUM_BUNDLE_INSTRUCTIONS:
        raise RuntimeError('Invalid bundle size for bundle. Expected {} instructions, but {} found.'.format(bundle_id,
                                                                                                            NUM_BUNDLE_INSTRUCTIONS,
                                                                                                            len(xinstrs[idx:])))
    current_bundle_cycle_count = 0  # Tracks number of cycles since last sync point (bundle start is the first sync point)
    current_bundle_latency = 0
    for xinstr in xinstr_bundle:
        if isinstance(xinstr, xinst.XStore):
            # Reset the latency because `xstore`s are synchronization points
            current_bundle_cycle_count = 0
            current_bundle_latency = 0
        else:
            assert xinstr.throughput <= xinstr.latency
            # Check if latency of new instruction at current cycle is greater than previous bundle latency
            if current_bundle_latency < current_bundle_cycle_count + xinstr.latency:
                current_bundle_latency = current_bundle_cycle_count + xinstr.latency
            # Advance cycle by instruction throughput
            current_bundle_cycle_count += xinstr.throughput

        if isinstance(xinstr, xinst.Exit):
            break  # Stop on exit

    return current_bundle_latency

def computeXBundleLatencies(xinstrs: list) -> list:
    """
    Computes latencies for all bundles of XInstructions.

    Parameters:
        xinstrs (list): A list of XInstructions.

    Returns:
        list: A list of latencies for each bundle.
    """
    print('WARNING: Check latency for `exit` XInstruction.')
    print('Computing x bundle latencies')
    retval = []
    total_xinstr = len(xinstrs)
    bundle_id = 0
    while xinstrs:
        if bundle_id % 1000 == 0:
            print("{}% - {}/{}".format((total_xinstr - len(xinstrs)) * 100 // total_xinstr, (total_xinstr - len(xinstrs)), total_xinstr))
        bundle = xinstrs[:NUM_BUNDLE_INSTRUCTIONS]
        xinstrs = xinstrs[NUM_BUNDLE_INSTRUCTIONS:]
        assert bundle[0].bundle == bundle_id and bundle[-1].bundle == bundle_id
        retval.append(computeXBundleLatency(bundle))
        bundle_id += 1

    print("100% - {0}/{0}".format(total_xinstr))

    return retval

def computeCBundleLatencies(cinstr_lines) -> list:
    """
    Computes latencies for all bundles of CInstructions.

    Parameters:
        cinstr_lines: An iterable of CInstruction lines.

    Returns:
        list: A list of latencies for each bundle.
    """
    print('Computing c bundle latencies')
    retval = []
    bundle_id = 0
    bundle_latency = 0
    for idx, c_line in enumerate(cinstr_lines):
        if idx % 500 == 0:
            print(idx)

        if c_line.strip():
            # remove comment and tokenize
            s_split = [s.strip() for s in c_line.split("#")[0].split(',')]
            if bundle_id < 0 and ('cnop' not in s_split[1]):
                raise RuntimeError('Invalid CInstruction detected after end of CInstQ')
            if 'ifetch' == s_split[1]:
                # New bundle
                assert int(s_split[2]) == bundle_id, f'ifetch, {s_split[2]} | expected {bundle_id}'
                retval.append(bundle_latency)
                bundle_id += 1
                bundle_latency = 0
            elif 'exit' in s_split[1]:
                # CInstQ terminate
                retval.append(bundle_latency)
                bundle_id = -1  # Will assert if more instructions after exit
            elif 'cstore' == s_split[1]:
                # Reset latency
                bundle_latency = 0
            else:
                instruction_throughput = 1
                if 'nop' in s_split[1]:
                    instruction_throughput = int(s_split[2])
                elif 'cload' in s_split[1]:
                    instruction_throughput = 4
                elif 'nload' in s_split[1]:
                    instruction_throughput = 4
                bundle_latency += instruction_throughput
    return retval[1:]

def main(input_dir: str, input_prefix: str = None):
    """
    Main function to check timing for register access and synchronization.

    Parameters:
        input_dir (str): Directory containing input files.
        input_prefix (str): Prefix for input files.
    """
    print("Starting")

    input_dir = makeUniquePath(input_dir)
    if not input_prefix:
        input_prefix = os.path.basename(input_dir)

    print('Input dir:', input_dir)
    print('Input prefix:', input_prefix)

    xinst_file = os.path.join(input_dir, input_prefix + ".xinst")
    cinst_file = os.path.join(input_dir, input_prefix + ".cinst")

    xinstrs = []
    with open(xinst_file, 'r') as f_in:
        for idx, line in enumerate(f_in):
            if idx % 50000 == 0:
                print(idx)
            if line.strip():
                # Remove comment
                s_split = line.split("#")[0].split(',')
                # Parse the line into an instruction
                instr_name = s_split[2].strip()
                b_parsed = False
                for xinstr_type in xinst.ASMISA_INSTRUCTIONS:
                    if xinstr_type.name == instr_name:
                        xinstr = xinstr_type.fromASMISALine(line)
                        xinstrs.append(xinstr)
                        b_parsed = True
                        break
                if not b_parsed:
                    raise ValueError(f'Could not parse line f{idx + 1}: {line}')

    # Check synchronization between C and X queues
    print("--------------")
    print("Checking synchronization between C and X queues...")
    xbundle_cycles = computeXBundleLatencies(xinstrs)
    with open(cinst_file, 'r') as f_in:
        cbundle_cycles = computeCBundleLatencies(f_in)

    if len(xbundle_cycles) != len(cbundle_cycles):
        raise RuntimeError('Mismatched bundles: {} xbundles vs. {} cbundles'.format(len(xbundle_cycles),
                                                                                    len(cbundle_cycles)))
    print("Comparing latencies...")
    bundle_cycles_violation_list = []
    for idx in range(len(xbundle_cycles)):
        if xbundle_cycles[idx] > cbundle_cycles[idx]:
            bundle_cycles_violation_list.append('Bundle {} | X {} cycles; C {} cycles'.format(idx,
                                                                                              xbundle_cycles[idx],
                                                                                              cbundle_cycles[idx]))

    # Check timings for register access
    print("--------------")
    print("Checking timings for register access...")
    violation_lst = []  # list(tuple(xinstr_idx, violating_idx, register: str, cycle_counter))
    for idx, xinstr in enumerate(xinstrs):
        if idx % 50000 == 0:
            print("{}% - {}/{}".format(idx * 100 // len(xinstrs), idx, len(xinstrs)))

        # Check bank conflict

        banks = set()
        for r, b in xinstr.srcs:
            if b in banks:
                violation_lst.append((idx + 1, f"Bank conflict source {b}", xinstr.name))
                break
            banks.add(b)

        banks = set()
        for r, b in xinstr.dsts:
            if b in banks:
                violation_lst.append((idx + 1, f"Bank conflict dests {b}", xinstr.name))
                break
            banks.add(b)

        if xinstr.name == 'move':
            # Make sure move is only moving from bank zero
            src_bank = xinstr.srcs[0][1]
            dst_bank = xinstr.dsts[0][1]
            if src_bank != 0:
                violation_lst.append((idx + 1, f"Move bank error sources {src_bank}", xinstr.name))
            if dst_bank == src_bank:
                violation_lst.append((idx + 1, f"Move bank error dests {dst_bank}", xinstr.name))

        # Check timing

        cycle_counter = xinstr.throughput
        for jdx in range(idx + 1, len(xinstrs)):
            if cycle_counter >= xinstr.latency:
                break  # Instruction outputs are ready
            next_xinstr = xinstrs[jdx]
            if next_xinstr.bundle != xinstr.bundle:
                assert(next_xinstr.bundle == xinstr.bundle + 1)
                break  # Different bundle

            # Check
            all_next_regs = set(next_xinstr.srcs + next_xinstr.dsts)
            for reg in xinstr.dsts:
                if reg in all_next_regs:
                    # Register is not ready and still used by an instruction
                    violation_lst.append((idx + 1, jdx + 1, f"r{reg[0]}b{reg[1]}", cycle_counter))

            cycle_counter += next_xinstr.throughput

    print("100% - {}/{}".format(idx, len(xinstrs)))

    # Check rshuffle separation
    print("--------------")
    print("Checking rshuffle separation...")
    rshuffle_violation_lst = []  # list(tuple(xinstr_idx, violating_idx, data_types: str, cycle_counter))
    print("WARNING: No distinction between `rshuffle` and `irshuffle`.")
    for idx, xinstr in enumerate(xinstrs):
        if idx % 50000 == 0:
            print("{}% - {}/{}".format(idx * 100 // len(xinstrs), idx, len(xinstrs)))

        if isinstance(xinstr, xinst.rShuffle):
            cycle_counter = xinstr.throughput
            for jdx in range(idx + 1, len(xinstrs)):
                if cycle_counter >= xinstr.latency:
                    break  # Instruction outputs are ready
                next_xinstr = xinstrs[jdx]
                if next_xinstr.bundle != xinstr.bundle:
                    assert(next_xinstr.bundle == xinstr.bundle + 1)
                    break  # Different bundle

                # Check
                if isinstance(next_xinstr, xinst.rShuffle):
                    if next_xinstr.data_type != xinstr.data_type:
                        # Mixing ntt and intt rshuffle inside the latency of first rshuffle
                        rshuffle_violation_lst.append((idx + 1, jdx + 1, f"{xinstr.data_type} != {next_xinstr.data_type}", cycle_counter))
                    elif cycle_counter < xinstr.special_latency_max \
                         and cycle_counter % xinstr.special_latency_increment != 0:
                        # Same data type
                        rshuffle_violation_lst.append((idx + 1, jdx + 1, f"{xinstr.data_type} == {next_xinstr.data_type}", cycle_counter))

                cycle_counter += next_xinstr.throughput

    print("100% - {}/{}".format(idx, len(xinstrs)))

    # Check bank conflicts with rshuffle
    print("--------------")
    print("Checking bank conflicts with rshuffle...")
    rshuffle_bank_violation_lst = []  # list(tuple(xinstr_idx, violating_idx, banks: str, cycle_counter))
    for idx, xinstr in enumerate(xinstrs):
        if idx % 50000 == 0:
            print("{}% - {}/{}".format(idx * 100 // len(xinstrs), idx, len(xinstrs)))

        if isinstance(xinstr, xinst.rShuffle):
            # No instruction should write to same bank at the write phase of rshuffle
            rshuffle_write_cycle = xinstr.latency - 1
            rshuffle_banks = set(bank for _, bank in xinstr.dsts)
            cycle_counter = xinstr.throughput
            for jdx in range(idx + 1, len(xinstrs)):
                if cycle_counter >= xinstr.latency:
                    break  # Instruction outputs are ready
                next_xinstr = xinstrs[jdx]
                if next_xinstr.bundle != xinstr.bundle:
                    assert(next_xinstr.bundle == xinstr.bundle + 1)
                    break  # Different bundle
                # Check
                if cycle_counter + next_xinstr.latency - 1 == rshuffle_write_cycle:
                    # Instruction writes in same cycle as rshuffle
                    # Check for bank conflicts
                    next_xinstr_banks = set(bank for _, bank in next_xinstr.dsts)
                    if rshuffle_banks & next_xinstr_banks:
                        rshuffle_bank_violation_lst.append((idx + 1, jdx + 1, "{} | banks: {}".format(next_xinstr.name, rshuffle_banks & next_xinstr_banks), cycle_counter))

                cycle_counter += next_xinstr.throughput

    print("100% - {}/{}".format(idx, len(xinstrs)))

    s_error_msgs = []

    if bundle_cycles_violation_list:
        # Log violation list
        print()
        for x in bundle_cycles_violation_list:
            print(x)
        s_error_msgs.append('Bundle cycle violations detected.')

    if violation_lst:
        # Log violation list
        print()
        for x in violation_lst:
            print(x)
        s_error_msgs.append('Register access violations detected.')

    if rshuffle_violation_lst:
        # Log violation list
        print()
        for x in rshuffle_violation_lst:
            print(x)
        s_error_msgs.append('rShuffle special latency violations detected.')

    if rshuffle_bank_violation_lst:
        # Log violation list
        print()
        for x in rshuffle_bank_violation_lst:
            print(x)
        s_error_msgs.append('rShuffle bank access violations detected.')

    if s_error_msgs:
        raise RuntimeError('\n'.join(s_error_msgs))

    print()
    print('No timing errors found.')

if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)
    print(module_name)

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("input_prefix", nargs="?")
    parser.add_argument("--isa_spec", default="", dest="isa_spec_file",
                        help=("Input ISA specification (.json) file."))
    args = parser.parse_args()

    args.isa_spec_file = XTC_SpecConfig.initialize_isa_spec(module_dir, args.isa_spec_file)
    print(f"ISA Spec: {args.isa_spec_file}")

    print()
    main(args.input_dir, args.input_prefix)

    print()
    print(module_name, "- Complete")