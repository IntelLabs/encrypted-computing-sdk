
from . import bload, bones, cexit, cload, cnop, cstore, csyncm, ifetch, kgload, kgseed, kgstart, nload, xinstfetch

# MInst aliases

BLoad = bload.Instruction
BOnes = bones.Instruction
CExit = cexit.Instruction
CLoad = cload.Instruction
CNop = cnop.Instruction
CStore = cstore.Instruction
CSyncm = csyncm.Instruction
IFetch = ifetch.Instruction
KGLoad = kgload.Instruction
KGSeed = kgseed.Instruction
KGStart = kgstart.Instruction
NLoad = nload.Instruction
XInstFetch = xinstfetch.Instruction

def factory() -> set:
    """
    Creates a set of all instruction classes.

    Returns:
        set: A set containing all instruction classes.
    """

    return { BLoad,
             BOnes,
             CExit,
             CLoad,
             CNop,
             CStore,
             CSyncm,
             IFetch,
             KGLoad,
             KGSeed,
             KGStart,
             NLoad,
             XInstFetch }
