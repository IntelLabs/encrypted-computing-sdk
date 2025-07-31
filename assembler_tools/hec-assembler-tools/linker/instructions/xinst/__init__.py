# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module provides all the supported X-instructions for the linker toolchain."""

from . import (
    add,
    intt,
    mac,
    maci,
    move,
    mul,
    muli,
    nop,
    ntt,
    rshuffle,
    sub,
    twintt,
    twntt,
    xstore,
)
from . import exit as exit_mod

# from . import copy as copy_mod

# XInst aliases

# XInsts with P-ISA equivalent
Add = add.Instruction
Sub = sub.Instruction
Mul = mul.Instruction
Muli = muli.Instruction
Mac = mac.Instruction
Maci = maci.Instruction
NTT = ntt.Instruction
INTT = intt.Instruction
TwNTT = twntt.Instruction
TwiNTT = twintt.Instruction
RShuffle = rshuffle.Instruction
# All other XInsts
Move = move.Instruction
XStore = xstore.Instruction
Exit = exit_mod.Instruction
Nop = nop.Instruction


def factory() -> set:
    """
    @brief Creates a set of all instruction classes.

    @return A set containing all instruction classes.
    """
    return {
        Add,
        Sub,
        Mul,
        Muli,
        Mac,
        Maci,
        NTT,
        INTT,
        TwNTT,
        TwiNTT,
        RShuffle,
        Move,
        XStore,
        Exit,
        Nop,
    }
