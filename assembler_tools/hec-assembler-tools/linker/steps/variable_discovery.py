# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief This module provides functionality to discover variable names in MInstructions and CInstructions.
"""
from assembler.memory_model.variable import Variable
from linker.instructions import minst, cinst
from linker.instructions.minst.minstruction import MInstruction
from linker.instructions.cinst.cinstruction import CInstruction


def discover_variables_spad(cinstrs: list):
    """
    @brief Finds Variable names used in a list of CInstructions.

    @param cinstrs List of CInstructions where to find variable names.
    @throws TypeError If an item in the list is not a valid CInstruction.
    @throws RuntimeError If an invalid Variable name is detected in a CInstruction.
    @return Yields an iterable over variable names identified in the listing
            of CInstructions specified.
    """
    for idx, cinstr in enumerate(cinstrs):
        if not isinstance(cinstr, CInstruction):
            raise TypeError(
                f"Item {idx} in list of MInstructions is not a valid MInstruction."
            )
        retval = None
        # TODO: Implement variable counting for CInst
        ###############
        # Raise NotImplementedError("Implement variable counting for CInst")
        if isinstance(cinstr, (cinst.BLoad, cinst.CLoad, cinst.BOnes, cinst.NLoad)):
            retval = cinstr.source
        elif isinstance(cinstr, cinst.CStore):
            retval = cinstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(
                    f'Invalid Variable name "{retval}" detected in instruction "{idx}, {cinstr.to_line()}"'
                )
            yield retval


def discover_variables(minstrs: list):
    """
    @brief Finds variable names used in a list of MInstructions.

    @param minstrs List of MInstructions where to find variable names.
    @throws TypeError If an item in the list is not a valid MInstruction.
    @throws RuntimeError If an invalid variable name is detected in an MInstruction.
    @return Yields an iterable over variable names identified in the listing
            of MInstructions specified.
    """
    for idx, minstr in enumerate(minstrs):
        if not isinstance(minstr, MInstruction):
            raise TypeError(
                f"Item {idx} in list of MInstructions is not a valid MInstruction."
            )
        retval = None
        if isinstance(minstr, minst.MLoad):
            retval = minstr.source
        elif isinstance(minstr, minst.MStore):
            retval = minstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(
                    f'Invalid Variable name "{retval}" detected in instruction "{idx}, {minstr.to_line()}"'
                )
            yield retval
