import argparse
import os

from xinst import xinstruction
from spec_config import XTC_SpecConfig

# Injects dummy bundles after bundle 1

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

def transferNextBundle(xinst_in_stream, xinst_out_stream, bundle_number):
    """
    Transfers the next bundle of instructions from input to output stream.

    Parameters:
        xinst_in_stream: The input stream for XInst instructions.
        xinst_out_stream: The output stream for XInst instructions.
        bundle_number: The current bundle number.
    """
    for _ in range(NUM_BUNDLE_INSTRUCTIONS):
        s_line = xinst_in_stream.readline().strip()
        # Must have an instruction
        assert s_line

        # Split line into tokens
        tokens, comment = xinstruction.tokenizeFromLine(s_line)
        tokens = list(tokens)
        tokens[0] = f"F{bundle_number}"

        s_line = ', '.join(tokens)
        if comment:
            s_line += f" # {comment}"

        print(s_line, file=xinst_out_stream)

def main(nbundles: int,
         input_dir: str,
         output_dir: str,
         input_prefix: str = None,
         output_prefix: str = None,
         b_use_exit: bool = True):
    """
    Main function to inject dummy bundles into instruction files.

    Parameters:
        nbundles (int): Number of dummy bundles to insert.
        input_dir (str): Directory containing input files.
        output_dir (str): Directory to save output files.
        input_prefix (str): Prefix for input files.
        output_prefix (str): Prefix for output files.
        b_use_exit (bool): Whether to use 'bexit' in dummy bundles.
    """
    print("Starting")

    input_dir = makeUniquePath(input_dir)
    if not input_prefix:
        input_prefix = os.path.basename(input_dir)
    output_dir = makeUniquePath(output_dir)
    if not output_prefix:
        output_prefix = os.path.basename(output_dir)

    print('Input dir:', input_dir)
    print('Input prefix:', input_prefix)
    print('Output dir:', output_dir)
    print('Output prefix:', output_prefix)
    print('Dummy bundles to insert:', nbundles)
    print('Use bexit:', b_use_exit)

    xinst_file_i = os.path.join(input_dir, input_prefix + ".xinst")
    cinst_file_i = os.path.join(input_dir, input_prefix + ".cinst")
    minst_file_i = os.path.join(input_dir, input_prefix + ".minst")

    xinst_file_o = os.path.join(output_dir, output_prefix + ".xinst")
    cinst_file_o = os.path.join(output_dir, output_prefix + ".cinst")
    minst_file_o = os.path.join(output_dir, output_prefix + ".minst")

    with open(xinst_file_i, 'r') as f_xinst_file_i, \
         open(cinst_file_i, 'r') as f_cinst_file_i, \
         open(minst_file_i, 'r') as f_minst_file_i:
        with open(xinst_file_o, 'w') as f_xinst_file_o, \
             open(cinst_file_o, 'w') as f_cinst_file_o, \
             open(minst_file_o, 'w') as f_minst_file_o:

            current_bundle = 0

            # Read xinst until first bundle is over
            num_xstores = 0
            for _ in range(NUM_BUNDLE_INSTRUCTIONS):
                line = f_xinst_file_i.readline().strip()
                assert line  # Cannot be EOF

                # Write line to output as is
                print(line, file=f_xinst_file_o)

                # Split line into tokens
                tokens, _ = xinstruction.tokenizeFromLine(line)

                # Must be bundle 0
                assert int(tokens[0][1:]) == current_bundle

                if tokens[2] == 'xstore':
                    # Encountered xstore
                    num_xstores += 1

            cinst_line_no = 0
            cinst_insertion_line_start = 0  # Track which line we started inserting dummy bundles into CInstQ
            cinst_insertion_line_count = 0  # Track how many lines of dummy bundles were inserted into CInstQ

            # Read cinst until first bundle is over
            while True:  # do-while
                line = f_cinst_file_i.readline().strip()
                # Cannot be EOF
                assert line

                # Write line to output as is
                print(line, file=f_cinst_file_o)

                # Split line into tokens
                tokens, _ = xinstruction.tokenizeFromLine(line)

                cinst_line_no += 1

                if tokens[1] == 'ifetch':
                    # Encountered first ifetch
                    assert int(tokens[2]) == current_bundle
                    break

            # Need to check if there are any xstores that have matching cstores
            for _ in range(num_xstores):
                line = f_cinst_file_i.readline().strip()
                # Cannot be EOF
                assert line

                # Write line to output as is
                print(line, file=f_cinst_file_o)

                # Split line into tokens
                tokens, _ = xinstruction.tokenizeFromLine(line)
                # Must be a matching cstore
                assert tokens[1] == 'cstore'

                cinst_line_no += 1

            current_bundle += 1  # Next bundle
            cinst_insertion_line_start = cinst_line_no  # Start inserting dummy bundles

            # Start inserting dummy bundles
            print("Inserting", nbundles, "dummy bundles...")
            if nbundles > 0:
                # Wait for last bundle to complete (use max possible bundle size)
                print(f"{cinst_line_no}, cnop, 2000", file=f_cinst_file_o)
                cinst_line_no += 1
            for idx in range(nbundles):
                if idx % 5000 == 0:
                    print("{}% - {}/{}".format(idx * 100 // nbundles, idx, nbundles))
                # Cinst
                print(f"{cinst_line_no}, ifetch, {current_bundle} # dummy bundle {idx + 1}", file=f_cinst_file_o)
                print(f"{cinst_line_no + 1}, cnop, 70", file=f_cinst_file_o)
                cinst_line_no += 2

                # Xinst
                if b_use_exit:
                    print(f"F{current_bundle}, 0, bexit # dummy bundle", file=f_xinst_file_o)
                else:
                    print(f"F{current_bundle}, 0, nop, 0", file=f_xinst_file_o)
                for _ in range(NUM_BUNDLE_INSTRUCTIONS - 1):
                    print(f"F{current_bundle}, 0, nop, 0", file=f_xinst_file_o)

                current_bundle += 1

            print("100% - {0}/{0}".format(nbundles))

            # Number of lines inserted in CInstQ
            cinst_insertion_line_count = cinst_line_no - cinst_insertion_line_start

            # Complete CInstQ and XInstQ
            print()
            print('Transferring remaining CInstQ and XInstQ...')
            print(cinst_line_no)
            while True:  # do-while
                if cinst_line_no % 50000 == 0:
                    print(cinst_line_no)

                line = f_cinst_file_i.readline().strip()
                if not line:  # EOF
                    break

                # Split line into tokens
                tokens, comment = xinstruction.tokenizeFromLine(line)
                tokens = list(tokens)

                tokens[0] = str(cinst_line_no)
                # Output line with correct line and bundle number
                if tokens[1] == 'ifetch':
                    # Ensure fetching correct bundle
                    tokens[2] = str(current_bundle)

                    # Output xinst bundle
                    transferNextBundle(f_xinst_file_i, f_xinst_file_o, current_bundle)
                    current_bundle += 1

                line = ', '.join(tokens)
                if comment:
                    line += f" # {comment}"

                print(line, file=f_cinst_file_o)
                cinst_line_no += 1

            print(cinst_line_no)

            # Fix sync points in MInstQ
            print()
            print('Fixing MInstQ sync points...')
            for idx, line in enumerate(f_minst_file_i):
                if idx % 5000 == 0:
                    print(idx)

                tokens, comment = xinstruction.tokenizeFromLine(line)
                assert int(tokens[0]) == idx, 'Unexpected line number mismatch in MInstQ.'

                tokens = list(tokens)
                # Process sync instruction
                if tokens[1] == 'msyncc':
                    ctarget_line_no = int(tokens[2])
                    if ctarget_line_no >= cinst_insertion_line_start:
                        ctarget_line_no += cinst_insertion_line_count
                    tokens[2] = str(ctarget_line_no)

                # Transfer minst line to output file
                line = ', '.join(tokens)
                if comment:
                    line += f" # {comment}"

                print(line, file=f_minst_file_o)

            print(idx)

if __name__ == "__main__":
    module_dir = os.path.dirname(__file__)
    module_name = os.path.basename(__file__)
    print(module_name)

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument("input_prefix", nargs="?")
    parser.add_argument("output_prefix", nargs="?")
    parser.add_argument("--isa_spec", default="", dest="isa_spec_file",
                        help=("Input ISA specification (.json) file."))
    parser.add_argument("-b", "--dummy_bundles", dest='nbundles', type=int, default=0)
    parser.add_argument("-ne", "--skip_exit", dest='b_use_exit', action='store_false')
    args = parser.parse_args()
    args.isa_spec_file = XTC_SpecConfig.initialize_isa_spec(module_dir, args.isa_spec_file)

    print(f"ISA Spec: {args.isa_spec_file}")
    print()

    main(args.nbundles, args.input_dir, args.output_dir,
         args.input_prefix, args.output_prefix, args.b_use_exit)

    print()
    print(module_name, "- Complete")