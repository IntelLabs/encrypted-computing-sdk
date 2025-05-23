
from . import mload, mstore, msyncc

# MInst aliases

MLoad = mload.Instruction
MStore = mstore.Instruction
MSyncc = msyncc.Instruction

def factory() -> set:
    """
    Creates a set of all instruction classes.

    Returns:
        set: A set containing all instruction classes.
    """
    return { MLoad,
             MStore,
             MSyncc }
