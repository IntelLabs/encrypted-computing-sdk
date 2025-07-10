# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module provides all the supported C-instructions for the linker toolchain."""

from . import (
    # Import all instruction modules
    bload,
    bones,
    cexit,
    cload,
    cnop,
    cstore,
    csyncm,
    ifetch,
    kgload,
    kgseed,
    kgstart,
    nload,
    xinstfetch,
)

# CInst aliases
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
    @brief Creates a set of all instruction classes.

    @return A set containing all instruction classes.
    """
    return {
        BLoad,
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
        XInstFetch,
    }
