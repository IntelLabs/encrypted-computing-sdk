import argparse
import os

# Searches the CInstQ and MInstQ to find deadlocks caused by sync instructions.
# Raises exception on first deadlock found, otherwise, completes successfully.

def makeUniquePath(path: str):
    """
    Normalizes and expand a given file path.

    Parameters:
        path (str): The file path to normalize and expand.

    Returns:
        str: The normalized and expanded file path.
    """
    return os.path.normcase(os.path.realpath(os.path.expanduser(path)))

def loadInstructions(istream) -> list:
    """
    Loads instructions from an input iterator.

    Parameters:
        istream: An iterator where each item is a string line considered to contain an instruction.

    Returns:
        list: A list of tuples. Each tuple contains a list of tokens from the comma-separated instruction and the comment.
    """
    retval = []
    for line in istream:
        line = line.strip()
        if line:
            # Separate comment
            s_instr = ""
            s_comment = ""
            comment_start_idx = line.find('#')
            if comment_start_idx < 0:
                s_instr = line
            else:
                s_instr = line[:comment_start_idx]
                s_comment = line[comment_start_idx + 1:]

            # Tokenize instruction
            s_instr = map(lambda s: s.strip(), s_instr.split(","))

            # Add instruction to collection
            retval.append((list(s_instr), s_comment))

    return retval

def findDeadlock(minsts: list, cinsts: list) -> tuple:
    """
    Searches the CInstQ and MInstQ to find the first deadlock.

    Parameters:
        minsts (list): List of MInst instructions.
        cinsts (list): List of CInst instructions.

    Returns:
        tuple: A tuple of indices where a deadlock was found, or None if no deadlock was found.
    """
    retval = None
    queue_order_watcher = 0
    deadlock_watcher = 0  # Tracks whenever a queue doesn't move: if both queues don't move back to back, a deadlock has occurred
    q = minsts[:]
    q1 = cinsts[:]
    while retval is None and (q and q1):
        # Remove all non-syncs from q
        sync_idx = len(q)
        for idx, instr in enumerate(q):
            if 'sync' in instr[1]:
                # Sync found
                sync_idx = idx
                break
        q = q[sync_idx:]
        if q:
            assert 'sync' in q[0][1], 'Next instruction in queue is not a sync!'

            if sync_idx != 0:
                # Queue moved: restart the deadlock watcher
                deadlock_watcher = 0

            if deadlock_watcher > 1:
                # Deadlock detected: neither queue moved
                if queue_order_watcher > 0:
                    # Swap queue to original input order
                    q, q1 = q1, q
                assert len(q) > 0 and len(q1) > 0
                # Report indices where deadlock occurred
                retval = (int(q[0][0]), int(q1[0][0]))
            else:
                # Check if syncing to an instruction already executed
                sync_to_q1_idx = int(q[0][2])
                if q1 and int(q1[0][0]) < sync_to_q1_idx:
                    # q1 is NOT past synced instruction

                    if sync_idx == 0:
                        # Queue didn't move
                        deadlock_watcher += 1

                    # Switch to execute q1
                    q, q1 = q1, q
                    queue_order_watcher = (queue_order_watcher + 1) % 2
                else:
                    # q1 is past synced instruction
                    q = q[1:]

    return retval

def main(input_dir: str, input_prefix: str = None):
    """
    Main function to check for deadlocks in instruction queues.

    Parameters:
        input_dir (str): The directory containing instruction files.
        input_prefix (str): The prefix for instruction files.
    """
    input_dir = makeUniquePath(input_dir)
    if not input_prefix:
        input_prefix = os.path.basename(input_dir)

    print('Deadlock test.')
    print()
    print('Input dir:', input_dir)
    print('Input prefix:', input_prefix)

    xinst_file = os.path.join(input_dir, input_prefix + ".xinst")
    cinst_file = os.path.join(input_dir, input_prefix + ".cinst")
    minst_file = os.path.join(input_dir, input_prefix + ".minst")

    with open(xinst_file, 'r') as f_xin:
        xinsts = loadInstructions(f_xin)
        xinsts = [x for (x, _) in xinsts]
    with open(cinst_file, 'r') as f_cin:
        cinsts = loadInstructions(f_cin)
        cinsts = [x for (x, _) in cinsts]
    with open(minst_file, 'r') as f_min:
        minsts = loadInstructions(f_min)
        minsts = [x for (x, _) in minsts]

    deadlock_indices = findDeadlock(minsts, cinsts)
    if deadlock_indices is not None:
        raise RuntimeError('Deadlock detected: MinstQ: {}, CInstQ: {}'.format(deadlock_indices[0], deadlock_indices[1]))

    print('No deadlock detected between CInstQ and MInstQ.')

if __name__ == "__main__":
    module_name = os.path.basename(__file__)
    print(module_name)
    print()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("input_prefix", nargs="?")
    args = parser.parse_args()

    main(args.input_dir, args.input_prefix)

    print()
    print(module_name, "- Complete")