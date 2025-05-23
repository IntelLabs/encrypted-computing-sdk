from .xinstruction import XInstruction
from . import add, mul, muli, mac, maci, ntt, intt, twntt, twintt, rshuffle, sub, move, xstore, nop
from . import exit as exit_mod

# XInst aliases

Add = add.Instruction
Mul = mul.Instruction
Muli = muli.Instruction
Mac = mac.Instruction
Maci = maci.Instruction
NTT = ntt.Instruction
iNTT = intt.Instruction
twNTT = twntt.Instruction
twiNTT = twintt.Instruction
rShuffle = rshuffle.Instruction
Sub = sub.Instruction
Move = move.Instruction
XStore = xstore.Instruction
Exit = exit_mod.Instruction
Nop = nop.Instruction

# collection of XInstructions with P-ISA or intermediate P-ISA equivalents
ASMISA_INSTRUCTIONS = ( Add, Mul, Muli, Mac, Maci, NTT, iNTT, twNTT, twiNTT, rShuffle, Sub, Move, XStore, Exit, Nop )
