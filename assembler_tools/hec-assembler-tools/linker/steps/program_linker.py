# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to link kernels into a program."""

from typing import Any, cast

from assembler.common.config import GlobalConfig
from assembler.instructions import cinst as ISACInst

import linker.kern_trace.kern_remap as kern_mapper
from linker import MemoryModel
from linker.instructions import cinst, dinst, minst
from linker.instructions.dinst.dinstruction import DInstruction
from linker.kern_trace import InstrAct, KernelInfo
from linker.kern_trace.kernel_info import CinstrMapEntry
from linker.loader import Loader
from linker.steps.program_linker_utils import (
    calculate_instruction_latency_adjustment,
    process_bload_instructions,
    remove_csyncm,
    search_minstrs_back,
    search_minstrs_forward,
)


class LinkedProgram:  # pylint: disable=too-many-instance-attributes
    """
    @class LinkedProgram
    @brief Encapsulates a linked program.

    This class offers facilities to track and link kernels, and
    outputs the linked program to specified output streams as kernels
    are linked.

    The program itself is not contained in this object.
    """

    def __init__(self, keep_hbm_boundary: bool = False, keep_spad_boundary: bool = False):
        """
        @brief Initializes a LinkedProgram object.
        """
        # Variable trackers
        self._minst_in_var_tracker: dict[str, int] = {}
        self._cinst_in_var_tracker: dict[str, int] = {}

        self._intermediate_vars: list = []
        self._spad_offset = 0
        self._keep_hbm_boundary = keep_hbm_boundary
        self._keep_spad_boundary = keep_spad_boundary

        self._minst_ostream = None
        self._cinst_ostream = None
        self._xinst_ostream = None
        self.__mem_model: MemoryModel
        self._bundle_offset = 0
        self._minst_line_offset = 0
        self._cinst_line_offset = 0
        self._kernel_count = 0  # Number of kernels linked into this program
        self._is_open = False

    def initialize(
        self,
        program_minst_ostream,
        program_cinst_ostream,
        program_xinst_ostream,
        mem_model: MemoryModel,
    ):
        """
        @brief Initializes a LinkedProgram object.

        @param program_minst_ostream Output stream for MInst instructions.
        @param program_cinst_ostream Output stream for CInst instructions.
        @param program_xinst_ostream Output stream for XInst instructions.
        @param mem_model (MemoryModel): Correctly initialized linker memory model. It must already contain the
            variables used throughout the program and their usage.
            This memory model will be modified by this object when linking kernels.
        @param suppress_comments (bool): Whether to suppress comments in the output.
        """
        self._minst_ostream = program_minst_ostream
        self._cinst_ostream = program_cinst_ostream
        self._xinst_ostream = program_xinst_ostream
        self.__mem_model = mem_model
        self._bundle_offset = 0
        self._minst_line_offset = 0
        self._cinst_line_offset = 0
        self._kernel_count = 0

        # Tracks whether this program is still accepting kernels to link
        self._is_open = True

    @property
    def keep_hbm_boundary(self) -> bool:
        """
        @brief Checks if the program is configured to keep HBM boundaries.

        @return bool True if HBM boundaries are kept, False otherwise.
        """
        return self._keep_hbm_boundary

    @property
    def keep_spad_boundary(self) -> bool:
        """
        @brief Checks if the program is configured to keep SPAD boundaries.

        @return bool True if SPAD boundaries are kept, False otherwise.
        """
        return self._keep_spad_boundary

    @property
    def is_open(self) -> bool:
        """
        @brief Checks if the program is open for linking new kernels.

        @return bool True if the program is open, False otherwise.
        """
        return self._is_open

    def close(self):
        """
        @brief Completes the program by terminating the queues with the correct exit code.

        Program will not accept new kernels to link after this call.

        @exception RuntimeError If the program is already closed.
        """
        if not self.is_open:
            raise RuntimeError("Program is already closed.")

        # Add closing `cexit`
        tokens = [str(self._cinst_line_offset), cinst.CExit.name]
        cexit_cinstr = cinst.CExit(tokens)
        print(
            f"{cexit_cinstr.idx}, {cexit_cinstr.to_line()}",
            file=self._cinst_ostream,
        )

        # Add closing msyncc
        tokens = [
            str(self._minst_line_offset),
            minst.MSyncc.name,
            str(self._cinst_line_offset + 1),
        ]
        cmsyncc_minstr = minst.MSyncc(tokens)
        print(
            f"{cmsyncc_minstr.idx}, {cmsyncc_minstr.to_line()}",
            end="",
            file=self._minst_ostream,
        )
        if not GlobalConfig.suppress_comments:
            print(" # terminating MInstQ", end="", file=self._minst_ostream)
        print(file=self._minst_ostream)

        # Program has been closed
        self._is_open = False

    def _validate_hbm_address(self, var_name: str, hbm_address: int):
        """
        @brief Validates the HBM address for a variable.

        @param var_name The name of the variable.
        @param hbm_address The HBM address to validate.

        @exception RuntimeError If the HBM address is invalid or does not match the declared address.
        """
        if self.__mem_model is None:
            raise RuntimeError("Memory model is not initialized.")

        if hbm_address < 0:
            raise RuntimeError(f'Invalid negative HBM address for variable "{var_name}".')
        if var_name in self.__mem_model.mem_info_vars:
            # Cast to dictionary to fix the indexing error
            mem_info_vars_dict = cast(dict[str, Any], self.__mem_model.mem_info_vars)
            if mem_info_vars_dict[var_name].hbm_address != hbm_address:
                raise RuntimeError(
                    f"Declared HBM address "
                    f"({mem_info_vars_dict[var_name].hbm_address})"
                    f" of mem Variable '{var_name}'"
                    f" differs from allocated HBM address ({hbm_address})."
                )

    def _validate_spad_address(self, var_name: str, spad_address: int):
        """
        @brief Validates the SPAD address for a variable (only available when no HBM).

        @param var_name The name of the variable.
        @param spad_address The SPAD address to validate.

        @exception RuntimeError If the SPAD address is invalid or does not match the declared address.
        """
        if self.__mem_model is None:
            raise RuntimeError("Memory model is not initialized.")

        # only available when no HBM
        assert not GlobalConfig.hasHBM

        # this method will validate the variable SPAD address against the
        # original HBM address, since there is no HBM
        if spad_address < 0:
            raise RuntimeError(f'Invalid negative SPAD address for variable "{var_name}".')
        if var_name in self.__mem_model.mem_info_vars:
            # Cast to dictionary to fix the indexing error
            mem_info_vars_dict = cast(dict[str, Any], self.__mem_model.mem_info_vars)
            if mem_info_vars_dict[var_name].hbm_address != spad_address:
                raise RuntimeError(
                    f"Declared HBM address"
                    f" ({mem_info_vars_dict[var_name].hbm_address})"
                    f" of mem Variable '{var_name}'"
                    f" differs from allocated HBM address ({spad_address})."
                )

    def _update_minsts(self, kernel: KernelInfo):
        """
        @brief Updates the MInsts in the kernel to offset to the current expected
        synchronization points, and convert variable placeholders/names into
        the corresponding HBM address.

        All MInsts in the kernel are expected to synchronize with CInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel with minstrs Dict of MInstructions to update.
        """
        if self.__mem_model is None:
            raise RuntimeError("Memory model is not initialized.")

        idx: int = 0
        while idx < len(kernel.minstrs):
            minstr = kernel.minstrs[idx]

            # Update msyncc
            if isinstance(minstr, minst.MSyncc):
                # If not the last MSyncc
                if idx < len(kernel.minstrs) - 1:
                    # Update msyncc target to new cinst and global program offset
                    minstr.target = kernel.cinstrs_map[minstr.target].cinstr.idx
                    minstr.target = minstr.target + self._cinst_line_offset

            # Change mload variable names into HBM addresses
            if isinstance(minstr, minst.MLoad):
                var_name = minstr.var_name

                if kernel.minstrs_map[idx].action != InstrAct.SKIP:
                    minstr.spad_address += self._spad_offset

                hbm_address = self.__mem_model.use_variable(var_name, self._kernel_count)
                self._validate_hbm_address(var_name, hbm_address)
                minstr.hbm_address = hbm_address
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""

            # Change mstore variable names into HBM addresses
            if isinstance(minstr, minst.MStore):
                var_name = minstr.var_name

                if kernel.minstrs_map[idx].action != InstrAct.SKIP:
                    minstr.spad_address += self._spad_offset

                hbm_address = self.__mem_model.use_variable(var_name, self._kernel_count)
                self._validate_hbm_address(var_name, hbm_address)
                minstr.hbm_address = hbm_address
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""

            idx += 1  # next instruction

    def _remove_and_merge_csyncm_cnop(self, kernel: KernelInfo):
        """
        @brief Remove csyncm instructions and merge consecutive cnop instructions.

        @param kernel_cinstrs List of CInstructions to process.
        """
        i = 0
        current_bundle = 0
        csyncm_count = 0
        while i < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[i]
            cinstr.idx = str(i)  # Update the line number

            # ------------------------------
            # This code block will remove csyncm instructions and keep track,
            # later adding their throughput into a cnop instruction before
            # a new bundle is fetched.

            if isinstance(cinstr, cinst.CNop):
                # Add the missing cycles to any cnop we encounter up to this point
                cinstr.cycles += csyncm_count * ISACInst.CSyncm.get_throughput()
                # Idle cycles to account for the csyncm have been added
                csyncm_count = 0

            if isinstance(cinstr, cinst.IFetch | cinst.NLoad | cinst.BLoad):
                if csyncm_count > 0:
                    # Extra cycles needed before scheduling next bundle
                    # Subtract 1 because cnop n, waits for n+1 cycles
                    cinstr_nop = cinst.CNop(
                        [
                            i,
                            cinst.CNop.name,
                            str(csyncm_count * ISACInst.CSyncm.get_throughput() - 1),
                        ]
                    )
                    kernel.cinstrs.insert(i, cinstr_nop)
                    # Insert instruction also in cinstrs_map
                    kernel.cinstrs_map.insert(i, CinstrMapEntry("", cinstr_nop, InstrAct.KEEP_SPAD))
                    csyncm_count = 0
                    i += 1
                if isinstance(cinstr, cinst.IFetch):
                    current_bundle = cinstr.bundle + 1
                    # Update the line number
                    cinstr.idx = i

            if isinstance(cinstr, cinst.CSyncm):
                # Remove instruction
                kernel.cinstrs_map[i].action = InstrAct.SKIP
                if current_bundle > 0:
                    csyncm_count += 1

            i += 1

            # ------------------------------
            # This code block differs from previous in that csyncm instructions
            # are replaced in place by cnops with the corresponding throughput.
            # This may result in several continuous cnop instructions, so,
            # the cnop merging code afterwards is needed to remove this side effect
            # if contiguous cnops are not desired.

            # if isinstance(cinstr, cinst.IFetch):
            #     current_bundle = cinstr.bundle + 1
            #
            # if isinstance(cinstr, cinst.CSyncm):
            #     # replace instruction by cnop
            #     kernel_cinstrs.pop(i)
            #     if current_bundle > 0:
            #          # Subtract 1 because cnop n, waits for n+1 cycles
            #         cinstr_nop = cinst.CNop([i, cinst.CNop.name, str(ISACInst.CSyncm.get_throughput())])
            #         kernel_cinstrs.insert(i, cinstr_nop)
            #
            # i += 1 # next instruction

        # Merge continuous cnop
        i = 0
        while i < len(kernel.cinstrs):
            if kernel.cinstrs_map[i].action != InstrAct.SKIP:
                cinstr = kernel.cinstrs[i]
                cinstr.idx = str(i)
                if isinstance(cinstr, cinst.CNop):
                    # Do look ahead
                    _next = i + 1
                    while kernel.cinstrs_map[_next].action == InstrAct.SKIP and _next < len(kernel.cinstrs):
                        _next += 1

                    if isinstance(kernel.cinstrs[_next], cinst.CNop):
                        # Add 1 because cnop n, waits for n+1 cycles
                        kernel.cinstrs[_next].cycles += cinstr.cycles + 1
                        kernel.cinstrs_map[i].action = InstrAct.SKIP
            i += 1

    def _update_cinsts_addresses_and_offsets(self, kernel_cinstrs: list):
        """
        @brief Updates bundle/target offsets and variable names to addresses for CInsts.

        All CInsts in the kernel are expected to start at bundle 0, and to
        synchronize with MInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel_cinstrs List of CInstructions to update.
        """
        if self.__mem_model is None:
            raise RuntimeError("Memory model is not initialized.")

        for i, cinstr in enumerate(kernel_cinstrs):
            # Update ifetch
            if isinstance(cinstr, cinst.IFetch):
                cinstr.bundle = cinstr.bundle + self._bundle_offset
            # Update xinstfetch
            if isinstance(cinstr, cinst.XInstFetch):
                raise NotImplementedError("`xinstfetch` not currently supported by linker.")
            # Update csyncm
            if isinstance(cinstr, cinst.CSyncm):
                # If not a NLoad CSyncm or not keeping HBM boundary, update target
                if i + 1 < len(kernel_cinstrs) and not isinstance(kernel_cinstrs[i + 1], cinst.NLoad) or self._keep_hbm_boundary:
                    cinstr.target = cinstr.target + self._minst_line_offset

            if not GlobalConfig.hasHBM:
                # Update all SPAD instruction variable names to be SPAD addresses
                # Change xload variable names into SPAD addresses
                if isinstance(
                    cinstr,
                    (cinst.BLoad, cinst.BOnes, cinst.CLoad, cinst.NLoad, cinst.CStore),
                ):
                    hbm_address = self.__mem_model.use_variable(cinstr.var_name, self._kernel_count)
                    self._validate_spad_address(cinstr.var_name, hbm_address)
                    cinstr.spad_address = hbm_address
                    cinstr.comment = f" var: {cinstr.var_name} - HBM({hbm_address})" + f";{cinstr.comment}" if cinstr.comment else ""

    def _update_cinst_kernel_hbm(self, kernel: KernelInfo):
        """
        @brief Updates CInsts for HBM mode, handling synchronization and address mapping.

        This method modifies the kernel's CInsts in place by updating synchronization points,
        adjusting cycles, and remapping SPAD addresses.

        @param kernel (KernelInfo): The kernel to update.
        """

        # Nothing to update in cinst if we are keeping the HBM boundary
        if self._keep_hbm_boundary:
            return

        idx: int = 0
        syncm_idx = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]

            if isinstance(cinstr, cinst.CSyncm):
                syncm_idx = cinstr.target
                # Update CSyncm target to the corresponding MInst
                if kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                    minstr = kernel.minstrs_map[syncm_idx].minstr
                    cinstr.target = minstr.idx

            elif isinstance(cinstr, (cinst.CLoad, cinst.BLoad, cinst.BOnes)):
                # Update CLoad/BLoad/BOnes SPAD addresses to new minst
                if kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                    minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, cinstr.spad_address)
                    minstr = kernel.minstrs_map[minstr_idx].minstr
                    cinstr.var_name = minstr.var_name

                    if cinstr.var_name in self._cinst_in_var_tracker:
                        cinstr.spad_address = self._cinst_in_var_tracker[cinstr.var_name]
                    else:
                        cinstr.spad_address = minstr.spad_address

            elif isinstance(cinstr, cinst.NLoad):
                # Update NLoad SPAD addresses to new minst
                minstr_idx = search_minstrs_forward(kernel.minstrs_map, 0, cinstr.spad_address)
                minstr = kernel.minstrs_map[minstr_idx].minstr
                cinstr.var_name = minstr.var_name

                if cinstr.var_name in self._cinst_in_var_tracker:
                    cinstr.spad_address = self._cinst_in_var_tracker[cinstr.var_name]
                else:
                    cinstr.spad_address = minstr.spad_address

            elif isinstance(cinstr, cinst.CStore):
                # Update CStore SPAD addresses to new minst
                if kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                    minstr_idx = search_minstrs_forward(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))
                    minstr = kernel.minstrs_map[minstr_idx].minstr
                    cinstr.var_name = minstr.var_name
                    cinstr.spad_address = minstr.spad_address
                    self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address

            idx += 1  # next instruction

    def _update_cinsts(self, kernel: KernelInfo):
        """
        @brief Updates the CInsts in the kernel to offset to the current expected bundle
        and synchronization points.

        All CInsts in the kernel are expected to start at bundle 0, and to
        synchronize with MInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel_cinstrs List of CInstructions to update.
        """
        if not GlobalConfig.hasHBM:
            self._remove_and_merge_csyncm_cnop(kernel)
        else:
            self._update_cinst_kernel_hbm(kernel)

        self._update_cinsts_addresses_and_offsets(kernel.cinstrs)

    def _update_xinsts(self, kernel_xinstrs: list) -> int:
        """
        @brief Updates the XInsts in the kernel to offset to the current expected bundle.

        All XInsts in the kernel are expected to start at bundle 0.
        Does not change the LinkedProgram object.

        @param kernel_xinstrs List of XInstructions to update.

        @return int The last bundle number after updating.
        """
        last_bundle = self._bundle_offset
        for xinstr in kernel_xinstrs:
            xinstr.bundle = xinstr.bundle + self._bundle_offset
            if last_bundle > xinstr.bundle:
                raise RuntimeError(f'Detected invalid bundle. Instruction bundle is less than previous: "{xinstr.to_line()}"')
            last_bundle = xinstr.bundle
        return last_bundle

    def link_kernel(self, kernel: KernelInfo):
        """
        @brief Links a specified kernel (given by its three instruction queues) into this
        program.

        The adjusted kernels will be appended into the output streams specified during
        construction of this object.

        @param kernel (KernelInfo): The kernel to link into this program.

        @exception RuntimeError If the program is closed and does not accept new kernels.
        """
        if not self.is_open:
            raise RuntimeError("Program is closed and does not accept new kernels.")

        # No minsts without HBM
        if not GlobalConfig.hasHBM:
            minstrs_list = []
        else:
            # extract all instructions from minstrs marked as KEEP_HBM in minstrs_map
            minstrs_list = [minstr_map.minstr for minstr_map in kernel.minstrs_map if minstr_map.action == InstrAct.KEEP_HBM]

        self._update_minsts(kernel)
        self._update_cinsts(kernel)
        self._bundle_offset = self._update_xinsts(kernel.xinstrs) + 1
        self._spad_offset += (kernel.spad_size + 1) if not self._keep_hbm_boundary else 0

        cinstrs_list = [cinstr_map.cinstr for cinstr_map in kernel.cinstrs_map if cinstr_map.action == InstrAct.KEEP_SPAD]

        # Append the kernel to the output

        for xinstr in kernel.xinstrs:
            print(xinstr.to_line(), end="", file=self._xinst_ostream)
            if not GlobalConfig.suppress_comments and xinstr.comment:
                print(f" #{xinstr.comment}", end="", file=self._xinst_ostream)
            print(file=self._xinst_ostream)

        for idx, cinstr in enumerate(cinstrs_list[:-1]):  # Skip the `cexit`
            line_no = idx + self._cinst_line_offset
            print(f"{line_no}, {cinstr.to_line()}", end="", file=self._cinst_ostream)
            if not GlobalConfig.suppress_comments and cinstr.comment:
                print(f" #{cinstr.comment}", end="", file=self._cinst_ostream)
            print(file=self._cinst_ostream)

        for idx, minstr in enumerate(minstrs_list[:-1]):  # Skip the exit `msyncc`
            line_no = idx + self._minst_line_offset
            print(f"{line_no}, {minstr.to_line()}", end="", file=self._minst_ostream)
            if not GlobalConfig.suppress_comments and minstr.comment:
                print(f" #{minstr.comment}", end="", file=self._minst_ostream)
            print(file=self._minst_ostream)

        self._minst_line_offset += (len(minstrs_list) - 1) if minstrs_list else 0  # Subtract last line that is getting removed
        self._cinst_line_offset += len(cinstrs_list) - 1  # Subtract last line that is getting removed
        self._kernel_count += 1  # Count the appended kernel

    def join_n_prune_dinst_kernels(self, kernels_dinstrs: list[list[DInstruction]]) -> list[DInstruction]:
        """
        @brief This method updates the class's intermediate (outputs of one kernel and inputs to the next)
        variables and merges a list of dinst kernels. In addition, it identifies and removes instructions
        that reference intermediate variables or perform redundant loads of the same variable. This ensures
        that variables carried across kernels are not duplicated, memory addresses remain consistent,
        and unnecessary operations are eliminated.

        @param kernels_dinstrs List of Kernels' DInstructions lists.

        @return list[DInstruction] A new instruction list representing the concatenated memory info.

        @exception ValueError If no DInstructions lists are provided for concatenation.
        """

        if not kernels_dinstrs:
            raise ValueError("No DInstructions lists provided for concatenation.")

        # Use dictionaries to track unique variables by name
        inputs: dict[str, DInstruction] = {}
        carry_over_vars: dict[str, DInstruction] = {}

        mem_address: int = 0
        new_kernels_dinstrs: list[DInstruction] = []
        for kernel_dinstrs in kernels_dinstrs:
            for cur_dinst in kernel_dinstrs:
                # Save the current output instruction to add at the end
                if isinstance(cur_dinst, dinst.DStore):
                    key = cur_dinst.var
                    carry_over_vars[key] = cur_dinst
                    continue

                if isinstance(cur_dinst, dinst.DLoad | dinst.DKeyGen):
                    key = cur_dinst.var
                    # Skip if the input is already in carry-over from previous outputs
                    if key in carry_over_vars:
                        carry_over_vars.pop(key)  # Remove from (output) carry-overs since it's now an input
                        self._intermediate_vars.append(key)
                        continue

                    # If the input is not (a previous output) in carry-over, add if it's not already (loaded) in inputs
                    if key not in inputs:
                        inputs[key] = cur_dinst
                        cur_dinst.address = mem_address
                        mem_address = mem_address + 1

                        new_kernels_dinstrs.append(cur_dinst)
                        continue

        # Add remaining carry-over variables to the new instructions
        for _, dintr in carry_over_vars.items():
            dintr.address = mem_address
            new_kernels_dinstrs.append(dintr)
            mem_address = mem_address + 1

        return new_kernels_dinstrs

    def prune_minst_kernel(self, kernel_info: KernelInfo):
        """
        @brief Removes unnecessary MInsts from the kernel.
        @param kernel_info KernelInfo object containing the kernel's MInsts.
        This method modifies the kernel's MInsts in place by removing MLoad instructions that load
        intermediate variables or already loaded variables, and MStore instructions that store
        intermediate variables. It also tracks loaded variables in the `_minst_in_var_tracker` list.
        """

        if self._keep_hbm_boundary:
            return

        # Initialize variables for tracking new indices and adjust_spad when instructions are removed
        adjust_idx: int = 0
        adjust_spad: int = 0

        spad_size: int = 0
        last_msyncc = None

        for idx, minstr in enumerate(kernel_info.minstrs):
            if isinstance(minstr, minst.MSyncc):
                last_msyncc = minstr
            elif isinstance(minstr, minst.MStore):
                # Remove mstore instructions that stores intermediate variables
                if minstr.var_name in self._intermediate_vars:
                    # Remove the MSyncc if it is the immediately previous instruction
                    if last_msyncc and last_msyncc.idx == idx - 1:
                        kernel_info.minstrs_map[idx - 1].action = InstrAct.SKIP
                        adjust_idx -= 1

                    # Take variable into account for spad if we are keeping the spad boundary
                    if self._keep_spad_boundary:
                        kernel_info.minstrs_map[idx].action = InstrAct.KEEP_SPAD
                        minstr.spad_address += adjust_spad  # Adjust source spad address
                        spad_size = minstr.spad_address
                    else:
                        kernel_info.minstrs_map[idx].action = InstrAct.SKIP
                        adjust_spad -= 1

                    adjust_idx -= 1

                # Keep instruction
                else:
                    # Calculate new SPAD Address
                    new_spad = minstr.spad_address + adjust_spad
                    # Adjust spad address if negative, this could leave gaps in the spad address space
                    if new_spad < 0:
                        adjust_spad -= new_spad
                        new_spad = 0

                    minstr.idx = minstr.idx + adjust_idx  # Update line number
                    minstr.spad_address += adjust_spad  # Adjust source spad address
                    spad_size = minstr.spad_address
            elif isinstance(minstr, minst.MLoad):
                # Remove mload instructions if variables already loaded
                if minstr.var_name in self._minst_in_var_tracker:
                    kernel_info.minstrs_map[idx].action = InstrAct.SKIP
                    minstr.spad_address = self._minst_in_var_tracker[minstr.var_name]  # Adjust dest spad address
                    adjust_spad -= 1
                    adjust_idx -= 1
                    continue

                # Remove mload instructions that load intermediate variables
                if minstr.var_name in self._intermediate_vars:
                    kernel_info.minstrs_map[idx].action = InstrAct.KEEP_SPAD if self._keep_spad_boundary else InstrAct.SKIP
                    adjust_spad -= 1
                    adjust_idx -= 1
                    continue

                # Calculate new SPAD Address
                new_spad = minstr.spad_address + adjust_spad
                # Adjust spad address if negative, this could leave gaps in the spad address space
                if new_spad < 0:
                    adjust_spad -= new_spad
                    new_spad = 0

                # Keep instruction
                minstr.spad_address = new_spad  # Adjust dest spad address
                minstr.idx = minstr.idx + adjust_idx  # Update line number
                spad_size = minstr.spad_address

                # Track loaded variables
                self._minst_in_var_tracker[minstr.var_name] = minstr.spad_address

            # Keep track of the spad size used by this kernel
            kernel_info.spad_size = max(spad_size, kernel_info.spad_size)

    def prune_cinst_kernel_hbm(self, kernel: KernelInfo):
        """
        @brief Prunes and updates CInsts for HBM mode, handling synchronization and address mapping.
        """
        # Nothing to prune in cinst if we are keeping the HBM boundary
        if self._keep_hbm_boundary:
            return

        adjust_idx: int = 0  # Used to adjust the index when removing CInsts
        adjust_cycles: int = 0

        syncm_idx: int = 0
        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]
            if isinstance(cinstr, cinst.IFetch):
                adjust_cycles = 0
            elif isinstance(cinstr, cinst.CNop):
                # Adjust CNop cycles based on removed instructions
                cinstr.cycles += adjust_cycles
            elif isinstance(cinstr, cinst.CSyncm):
                # Keeping track of the minst
                syncm_idx = cinstr.target
            elif isinstance(cinstr, (cinst.CLoad, cinst.BLoad, cinst.BOnes)):
                minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))

                cinstr.var_name = kernel.minstrs_map[minstr_idx].minstr.var_name

                # Remove CLoad/BLoad/BOnes instructions if minstr action is SKIP
                if kernel.minstrs_map[minstr_idx].action == InstrAct.SKIP:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    adjust_idx -= 1
                    adjust_cycles += calculate_instruction_latency_adjustment(cinstr)

                    # Remove any csyncm instructions before this load
                    _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
                    adjust_idx += _idx
                    adjust_cycles += _cycles

                # Check if the variable is an intermediate variable
                elif cinstr.var_name in self._intermediate_vars:
                    # Remove any csyncm instruction before this load
                    _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
                    adjust_idx += _idx
                    adjust_cycles += _cycles

            elif isinstance(cinstr, cinst.CStore):
                minstr_idx = search_minstrs_forward(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))

                cinstr.var_name = kernel.minstrs_map[minstr_idx].minstr.var_name

                # Remove CStore instructions if minstr action is SKIP
                if kernel.minstrs_map[minstr_idx].action == InstrAct.SKIP:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    adjust_idx -= 1
                    adjust_cycles += ISACInst.CStore.get_latency()
                else:
                    cinstr.idx += adjust_idx  # Update line number

                # Check if the variable is an intermediate variable
                if cinstr.var_name in self._intermediate_vars:
                    # CSyncm no needed for intermediate variables
                    _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx + 1)
                    adjust_idx += _idx
                    adjust_cycles += _cycles

            idx += 1  # next instruction

    def prune_cinst_kernel_no_hbm(self, kernel: KernelInfo):
        """
        @brief Prunes and updates CInsts for HBM mode, handling synchronization and address mapping.
        """

        if self._keep_hbm_boundary:
            return

        adjust_cycles: int = 0

        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]
            # Update csyncm
            if isinstance(cinstr, cinst.IFetch):
                adjust_cycles = 0
            elif isinstance(cinstr, cinst.CNop):
                cinstr.cycles += adjust_cycles
            elif isinstance(cinstr, cinst.BLoad):
                idx = process_bload_instructions(kernel.cinstrs, kernel.cinstrs_map, self._cinst_in_var_tracker, idx)

                if cinstr.var_name not in self._cinst_in_var_tracker:
                    self._cinst_in_var_tracker[cinstr.var_name] = 0

            elif isinstance(cinstr, (cinst.CLoad, cinst.BOnes)):
                # Remove CLoad/BLoad/BOnes instructions if variable already loaded
                if cinstr.var_name in self._cinst_in_var_tracker:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    adjust_cycles += calculate_instruction_latency_adjustment(cinstr)
                # Check if the variable is an intermediate variable
                elif cinstr.var_name in self._intermediate_vars and not self._keep_spad_boundary:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                # Keep instruction
                else:
                    self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address

            elif isinstance(cinstr, cinst.CStore) and cinstr.var_name in self._intermediate_vars and not self._keep_spad_boundary:
                kernel.cinstrs_map[idx].action = InstrAct.SKIP

            idx += 1  # next instruction

    def link_kernels_to_files(
        self,
        kernels_info: list[KernelInfo],
        output_files,
        mem_model,
        verbose_stream=None,
    ):
        """
        @brief Links input kernels and writes the output to the specified files.

        @param kernels_info List of KernelInfo for input kernels.
        @param output_files KernelInfo for output.
        @param mem_model Memory model to use.
        @param verbose_stream Stream for verbose output.
        """
        with (
            open(output_files.minst, "w", encoding="utf-8") as fnum_output_minst,
            open(output_files.cinst, "w", encoding="utf-8") as fnum_output_cinst,
            open(output_files.xinst, "w", encoding="utf-8") as fnum_output_xinst,
        ):
            self.initialize(fnum_output_minst, fnum_output_cinst, fnum_output_xinst, mem_model)

            for idx, kernel in enumerate(kernels_info):
                if verbose_stream:
                    print(
                        f"[ {idx * 100 // len(kernels_info): >3}% ]",
                        kernel.prefix,
                        file=verbose_stream,
                    )

                if GlobalConfig.hasHBM:
                    kernel.cinstrs = Loader.load_cinst_kernel_from_file(kernel.cinst)
                    kern_mapper.remap_m_c_instrs_vars(kernel.cinstrs, kernel.hbm_remap_dict)
                    self.prune_cinst_kernel_hbm(kernel)

                kernel.xinstrs = Loader.load_xinst_kernel_from_file(kernel.xinst)

                self.link_kernel(kernel)

            if verbose_stream:
                print("[ 100% ] Finalizing output", output_files.prefix, file=verbose_stream)

            self.close()

    def flush_buffers(self):
        """
        @brief Flushes the CInst input variable tracker.

        This method clears the list of input variables used in CInsts.
        """
        self._cinst_in_var_tracker.clear()
        self._minst_in_var_tracker.clear()
        self._spad_offset = 0
