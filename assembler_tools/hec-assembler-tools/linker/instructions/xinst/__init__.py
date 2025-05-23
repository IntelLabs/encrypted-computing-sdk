from . import add, sub, mul, muli, mac, maci, ntt, intt, twntt, twintt, rshuffle, move, xstore, nop
from . import exit as exit_mod
#from . import copy as copy_mod

# XInst aliases

# XInsts with P-ISA equivalent
Add = add.Instruction
Sub = sub.Instruction
Mul = mul.Instruction
Muli = muli.Instruction
Mac = mac.Instruction
Maci = maci.Instruction
NTT = ntt.Instruction
iNTT = intt.Instruction
twNTT = twntt.Instruction
twiNTT = twintt.Instruction
rShuffle = rshuffle.Instruction
# All other XInsts
Move = move.Instruction
XStore = xstore.Instruction
Exit = exit_mod.Instruction
Nop = nop.Instruction

def factory() -> set:
    """
    Creates a set of all instruction classes.

    Returns:
        set: A set containing all instruction classes.
    """
    return { Add,
             Sub,
             Mul,
             Muli,
             Mac,
             Maci,
             NTT,
             iNTT,
             twNTT,
             twiNTT,
             rShuffle,
             Move,
             XStore,
             Exit,
             Nop }
