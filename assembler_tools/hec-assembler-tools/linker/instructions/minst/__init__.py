# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""@brief This module provides all the supported M-instructions for the linker toolchain."""

from . import mload, mstore, msyncc

# MInst aliases

MLoad = mload.Instruction
MStore = mstore.Instruction
MSyncc = msyncc.Instruction


def factory() -> set:
    """
    @brief Creates a set of all instruction classes.

    @return A set containing all instruction classes.
    """
    return {MLoad, MStore, MSyncc}
