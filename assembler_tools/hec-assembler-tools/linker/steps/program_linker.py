# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to link kernels into a program."""

from typing import Any, cast

from assembler.common import dinst
from assembler.common.config import GlobalConfig
from assembler.common.dinst.dinstruction import DInstruction
from assembler.instructions import cinst as ISACInst
import linker.kern_trace.kern_remap as kern_mapper
from linker import MemoryModel
from linker.instructions import cinst, minst, xinst
from linker.kern_trace import InstrAct, KernelInfo
from linker.kern_trace.kernel_info import CinstrMapEntry
from linker.loader import Loader
from linker.steps.program_linker_utils import (
    XStoreMoveMapEntry,
    get_instruction_lat,
    get_instruction_tp,
    proc_seq_bloads,
    remove_csyncm,
    search_cinstrs_back,
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
        self._xstores_map: dict[str, XStoreMoveMapEntry] = {}
        self._var_name_by_reg: dict[str, str] = {}  # Maps register names to variable names for tracking
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

        self._last_cq_tp = 0  # CInst queue thrpughput used since last sync point

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
        the corresponding HBM addresses.

        All MInsts in the kernel are expected to synchronize with CInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel with minstrs Dict of MInstructions to update.
        """
        if self.__mem_model is None:
            raise RuntimeError("Memory model is not initialized.")

        idx: int = 0
        while idx < len(kernel.minstrs):
            minstr = kernel.minstrs[idx]
            # Update MSyncc to new target index + global kernel offset
            if isinstance(minstr, minst.MSyncc):
                # If not the last MSyncc
                if idx < len(kernel.minstrs) - 1:
                    minstr.target = kernel.cinstrs_map[minstr.target].cinstr.idx
                    minstr.target = minstr.target + self._cinst_line_offset
            # Change MLoad variable names into HBM addresses
            if isinstance(minstr, minst.MLoad):
                var_name = minstr.var_name
                # Update SPAD address with offset if not skipping
                if kernel.minstrs_map[idx].action != InstrAct.SKIP:
                    minstr.spad_address += self._spad_offset
                # Get HBM address from memory model
                hbm_address = self.__mem_model.use_variable(var_name, self._kernel_count)
                self._validate_hbm_address(var_name, hbm_address)
                minstr.hbm_address = hbm_address
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""
            # Change mstore variable names into HBM addresses
            if isinstance(minstr, minst.MStore):
                var_name = minstr.var_name
                # Update SPAD address with offset if not skipping
                if kernel.minstrs_map[idx].action != InstrAct.SKIP:
                    minstr.spad_address += self._spad_offset
                # Get HBM address from memory model
                hbm_address = self.__mem_model.use_variable(var_name, self._kernel_count)
                self._validate_hbm_address(var_name, hbm_address)
                minstr.hbm_address = hbm_address
                minstr.comment = f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}" if minstr.comment else ""

            idx += 1  # Next instruction

    def _remove_and_merge_csyncm_cnop(self, kernel: KernelInfo):
        """
        @brief Remove csyncm instructions and merge consecutive cnop instructions.

        @param kernel with cinstrs List of CInstructions to process.
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
                    while _next < len(kernel.cinstrs) and kernel.cinstrs_map[_next].action == InstrAct.SKIP:
                        _next += 1

                    if _next < len(kernel.cinstrs) and isinstance(kernel.cinstrs[_next], cinst.CNop):
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
            # Update ifetch to global bundle offset
            if isinstance(cinstr, cinst.IFetch):
                cinstr.bundle = cinstr.bundle + self._bundle_offset
            # Update xinstfetch
            if isinstance(cinstr, cinst.XInstFetch):
                raise NotImplementedError("`xinstfetch` not currently supported by linker.")
            # Update csyncm target to global minst line offset
            if isinstance(cinstr, cinst.CSyncm):
                # NLoad CSyncm targets not updated unless we are keeping HBM boundary.
                # As result, they end up pointing to first ntt's tables loaded.
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

        syncm_idx: int = 0  # Last sync point to minst

        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]
            if isinstance(cinstr, cinst.CSyncm):
                syncm_idx = cinstr.target
                # If not skipping, update CSyncm target to new minst index
                if kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                    minstr = kernel.minstrs_map[syncm_idx].minstr
                    cinstr.target = minstr.idx
            elif isinstance(cinstr, (cinst.CLoad, cinst.BLoad, cinst.BOnes)):
                # Update CLoad/BLoad/BOnes SPAD addresses to new minst
                if kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                    minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, cinstr.spad_address)
                    minstr = kernel.minstrs_map[minstr_idx].minstr
                    cinstr.var_name = minstr.var_name
                    # If variable already in tracker, use that SPAD address
                    if cinstr.var_name in self._cinst_in_var_tracker:
                        cinstr.spad_address = self._cinst_in_var_tracker[cinstr.var_name]
                    else:
                        cinstr.spad_address = minstr.spad_address
                        self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address
            elif isinstance(cinstr, cinst.NLoad):
                pass
                # No need to update, all ntt tables are placed in the same SPAD addresses.
                # As a result, this will point to first loaded tables.
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

        # Nothing to prune if we are keeping transactions to the HBM
        if self._keep_hbm_boundary:
            return

        # Initialize variables for tracking new indices and adjusting SPAD addresses when instructions are removed
        adjust_idx: int = 0
        adjust_spad: int = 0

        spad_size: int = 0  # Tracks the maximum SPAD address used in this kernel
        last_msyncc = None  # Tracks the last MSyncc instruction

        for idx, minstr in enumerate(kernel_info.minstrs):
            if isinstance(minstr, minst.MSyncc):
                # Track the last MSyncc instruction
                last_msyncc = minstr
            elif isinstance(minstr, minst.MStore):
                # Remove from MInst (HBM) the MStore instructions for intermediate variables
                if minstr.var_name in self._intermediate_vars:
                    # Remove the MSyncc if it is the immediately previous instruction
                    if last_msyncc and last_msyncc.idx == idx - 1:
                        kernel_info.minstrs_map[idx - 1].action = InstrAct.SKIP
                        adjust_idx -= 1

                    # Determine SPAD action based on xstore map
                    action = InstrAct.SKIP
                    if minstr.var_name in self._xstores_map:
                        action = self._xstores_map[minstr.var_name].action

                    # Take variable into account for spad if we are keeping the spad boundary
                    if self._keep_spad_boundary or action == InstrAct.KEEP_SPAD:
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
                    # Adjust spad address if negative. ** Note: this could leave gaps in the spad address space
                    if new_spad < 0:
                        adjust_spad -= new_spad
                        new_spad = 0

                    minstr.idx = minstr.idx + adjust_idx  # Update line number
                    minstr.spad_address += adjust_spad  # Adjust source spad address
                    spad_size = minstr.spad_address
            elif isinstance(minstr, minst.MLoad):
                # Remove MLoad instructions if variable is already loaded
                if minstr.var_name in self._minst_in_var_tracker:
                    # Keep psi, rlk, pHalf and ipsi loads from spad
                    if minstr.var_name.startswith(("psi", "rlk", "ipsi", "phalf")):
                        kernel_info.minstrs_map[idx].action = InstrAct.KEEP_SPAD
                    else:
                        kernel_info.minstrs_map[idx].action = InstrAct.SKIP
                    # Update spad address
                    minstr.spad_address = self._minst_in_var_tracker[minstr.var_name]
                    adjust_spad -= 1
                    adjust_idx -= 1
                    continue

                # Remove MLoad instructions that load intermediate variables
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

                # Keep & update instruction
                minstr.spad_address = new_spad  # Adjust dest spad address
                minstr.idx = minstr.idx + adjust_idx  # Update line number
                spad_size = minstr.spad_address

                # Track loaded variables
                self._minst_in_var_tracker[minstr.var_name] = minstr.spad_address

            # Keep track of the spad size used by this kernel
            kernel_info.spad_size = max(spad_size, kernel_info.spad_size)

    def _insert_latency_cnop_if_needed(self, bundle: int, prev_kernel: KernelInfo, last_cq_tp: int) -> None:
        """
        @brief Insert a CNop into prev_kernel to cover remaining XInst bundle latency.

        @param prev_kernel Previous kernel (may be None).
        @param idx Current IFetch index in the new kernel.
        @param last_cq_tp Throughput accumulated in the previous kernel C queue.
        """

        # Check cycles against xinst bundle latency of previous kernel
        if bundle == 0 and prev_kernel is not None:
            # First ifetch, account for last xinst latency
            last_xq_lat = 0
            x_idx = len(prev_kernel.xinstrs) - 1
            prev_bundle = prev_kernel.xinstrs[x_idx].bundle
            while (
                x_idx >= 0 and prev_kernel.xinstrs[x_idx].bundle == prev_bundle and not isinstance(prev_kernel.xinstrs[x_idx], xinst.XStore)
            ):
                last_xq_lat += get_instruction_lat(prev_kernel.xinstrs[x_idx])
                x_idx -= 1

            # Adjust cycles if last xinst bundle latency is greater than last CQueue throughput
            if last_cq_tp < last_xq_lat:
                wait_cycles = last_xq_lat - last_cq_tp
                # Insert on previous kernel. This keeps current instructions on its original idx.
                # Usefull to find instructions by old target when updating an MSyncc with new idx
                ins_idx = len(prev_kernel.cinstrs) - 2  # Before the cexit
                cinstr_nop = cinst.CNop(
                    [
                        ins_idx,
                        cinst.CNop.name,
                        str(wait_cycles - ISACInst.CNop.get_throughput()),  # Subtract 1 because cnop n, waits for n+1 cycles
                    ],
                    f" Inserted by linker to account for last XInst bundle latency ({last_xq_lat} cycles)",
                )
                prev_kernel.cinstrs.insert(ins_idx, cinstr_nop)  # Insert before the `cexit`
                # Insert instruction also in cinstrs_map
                prev_kernel.cinstrs_map.insert(ins_idx, CinstrMapEntry("", cinstr_nop, InstrAct.KEEP_SPAD))

    def _handle_cload_prune_hbm(self, cinstr: cinst.CLoad, kernel: KernelInfo, idx: int, syncm_idx: int) -> tuple[int, int]:
        """
        @brief Handle a CLoad instruction during HBM pruning.
        @return (adjust_idx, removed_cycles) updated values after processing.
        """
        adjust_idx: int = 0
        removed_cycles: int = 0
        minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))

        # Intermediate variable path
        if cinstr.var_name in self._intermediate_vars:
            if cinstr.var_name in self._xstores_map:
                action = self._xstores_map[cinstr.var_name].action
                if action == InstrAct.KEEP_SPAD:
                    self._last_cq_tp += ISACInst.CLoad.get_throughput()
                else:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    adjust_idx -= 1
                    removed_cycles += ISACInst.CLoad.get_throughput()
            _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
            adjust_idx += _idx
            removed_cycles += _cycles
            return adjust_idx, removed_cycles

        # Minstr skipped
        if kernel.minstrs_map[minstr_idx].action == InstrAct.SKIP:
            kernel.cinstrs_map[idx].action = InstrAct.SKIP
            adjust_idx -= 1
            removed_cycles += get_instruction_tp(cinstr)
            _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
            adjust_idx += _idx
            removed_cycles += _cycles
            return adjust_idx, removed_cycles

        # Already loaded
        if cinstr.var_name in self._cinst_in_var_tracker:
            _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
            adjust_idx += _idx
            removed_cycles += _cycles
            self._last_cq_tp += ISACInst.CLoad.get_throughput()
            return adjust_idx, removed_cycles

        # First time load
        self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address
        self._last_cq_tp += ISACInst.CLoad.get_throughput()
        return adjust_idx, removed_cycles

    def prune_cinst_kernel_hbm(self, kernel: KernelInfo, prev_kernel: KernelInfo):
        """
        @brief Prunes CInsts for HBM mode.
        """
        # Nothing to prune in cinst if we are keeping transactions to the HBM
        if self._keep_hbm_boundary:
            return

        adjust_idx: int = 0  # Used to adjust the index when removing CInsts
        removed_cycles: int = 0  # Used to adjust cnop cycles when removing CInsts
        syncm_idx: int = 0  # Last sync point to minst

        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]

            if isinstance(cinstr, cinst.IFetch):
                self._insert_latency_cnop_if_needed(cinstr.bundle, prev_kernel, self._last_cq_tp)
                # Sync point, reset cycle counts
                removed_cycles = 0
                self._last_cq_tp = 0

            elif isinstance(cinstr, cinst.CNop):
                # Use exsting CNops to restore cycles based on removed instructions
                if removed_cycles > 0:
                    cinstr.cycles += removed_cycles
                    cinstr.comment = (
                        cinstr.comment + "; " if cinstr.comment else ""
                    ) + f" Adjusted ({removed_cycles} cycles) by linker to account for removed instructions"
                removed_cycles = 0
                self._last_cq_tp += ISACInst.CNop.get_throughput() + cinstr.cycles

            elif isinstance(cinstr, cinst.CSyncm):
                # Keeping track of the minst sync point
                syncm_idx = cinstr.target

            elif isinstance(cinstr, (cinst.BLoad, cinst.BOnes)):
                # Remove BLoad/BOnes instructions if minstr action is SKIP
                minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))
                if kernel.minstrs_map[minstr_idx].action == InstrAct.SKIP:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    adjust_idx -= 1
                    removed_cycles += get_instruction_tp(cinstr)
                    # Remove any csyncm instructions before this load; not needed anymore.
                    _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx - 1)
                    adjust_idx += _idx
                    removed_cycles += _cycles
                else:
                    self._last_cq_tp += get_instruction_tp(cinstr)
            # Handle CLoad instructions
            elif isinstance(cinstr, cinst.CLoad):
                _idx, _cycles = self._handle_cload_prune_hbm(cinstr, kernel, idx, syncm_idx)
                adjust_idx += _idx
                removed_cycles += _cycles
            # Check if the CStore variable is an intermediate variable
            elif isinstance(cinstr, cinst.CStore) and cinstr.var_name in self._intermediate_vars:
                # CSyncm no needed for intermediate variables if there is no HBM boundary.
                _idx, _cycles = remove_csyncm(kernel.cinstrs, kernel.cinstrs_map, idx + 1)
                adjust_idx += _idx
                removed_cycles += _cycles
                # Check action for this intermediate variable
                if cinstr.var_name in self._xstores_map:
                    action = self._xstores_map[cinstr.var_name].action
                    if action == InstrAct.KEEP_SPAD:
                        cinstr.idx += adjust_idx  # Update line number
                        # Reset count, not need to adjust cycles as cstores are blocking
                        removed_cycles = 0
                        self._last_cq_tp = 0
                    else:
                        kernel.cinstrs_map[idx].action = InstrAct.SKIP
                        adjust_idx -= 1
                        removed_cycles += ISACInst.CStore.get_throughput()

            elif kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                # Keep track of throughput for other kept instructions
                self._last_cq_tp += get_instruction_tp(cinstr)
                cinstr.idx += adjust_idx  # Update line number

            idx += 1  # next instruction

    def _handle_cload_prune_no_hbm(self, cinstr: cinst.CLoad, kernel: KernelInfo, idx: int) -> int:
        """
        @brief Handle a CLoad instruction in no-HBM mode, updating trackers and actions.

        @param cinstr The CLoad instruction.
        @param kernel KernelInfo containing instruction/action maps.
        @param idx Index of the instruction inside kernel.cinstrs.
        @return int Additional removed cycle count contributed by this instruction.
        """
        removed_delta = 0
        # Already loaded?
        if cinstr.var_name in self._cinst_in_var_tracker:
            kernel.cinstrs_map[idx].action = InstrAct.SKIP
            removed_delta += ISACInst.CLoad.get_throughput()
            return removed_delta

        # Intermediate variable with xstore decision?
        if cinstr.var_name in self._intermediate_vars and cinstr.var_name in self._xstores_map:
            action = self._xstores_map[cinstr.var_name].action
            if action == InstrAct.KEEP_SPAD:
                self._last_cq_tp += ISACInst.CLoad.get_throughput()
            else:
                kernel.cinstrs_map[idx].action = InstrAct.SKIP
                removed_delta += ISACInst.CLoad.get_throughput()
            return removed_delta

        # Track new load unless special table (psi / rlk / ipsi / pHalf)
        if not cinstr.var_name.startswith(("psi", "rlk", "ipsi", "phalf")):
            self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address
            self._last_cq_tp += ISACInst.CLoad.get_throughput()
        return removed_delta

    def prune_cinst_kernel_no_hbm(self, kernel: KernelInfo, prev_kernel: KernelInfo):
        """
        @brief Prunes CInsts of unnecessary memory transactions for HBM mode.
        """

        # Nothing to prune if keeping higher level boundary
        if self._keep_hbm_boundary:
            return

        removed_cycles: int = 0  # Used to keep track of removed cycles

        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]
            if isinstance(cinstr, cinst.IFetch):
                self._insert_latency_cnop_if_needed(cinstr.bundle, prev_kernel, self._last_cq_tp)
                # Sync point: reset cycle counts
                removed_cycles = 0
                self._last_cq_tp = 0
            elif isinstance(cinstr, cinst.CNop):
                # Use exsting CNops to restore removed cycles
                if removed_cycles > 0:
                    cinstr.cycles += removed_cycles
                    cinstr.comment = (
                        cinstr.comment + "; " if cinstr.comment else ""
                    ) + f" Adjusted ({removed_cycles} cycles) by linker to account for removed instructions"
                removed_cycles = 0
                self._last_cq_tp += ISACInst.CNop.get_throughput() + cinstr.cycles
            elif isinstance(cinstr, cinst.BLoad):
                # Process consecutive BLoads
                tp, idx = proc_seq_bloads(kernel.cinstrs, kernel.cinstrs_map, self._cinst_in_var_tracker, idx)
                self._last_cq_tp += tp
                # Track loaded variable
                if cinstr.var_name not in self._cinst_in_var_tracker:
                    self._cinst_in_var_tracker[cinstr.var_name] = 0
            elif isinstance(cinstr, cinst.BOnes):
                # Remove BOnes instructions if variable already loaded
                if cinstr.var_name in self._cinst_in_var_tracker:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    removed_cycles += get_instruction_tp(cinstr)
                # Otherwise, track loaded variable
                else:
                    self._cinst_in_var_tracker[cinstr.var_name] = cinstr.spad_address
                    self._last_cq_tp += ISACInst.BOnes.get_throughput()
            elif isinstance(cinstr, cinst.CLoad):
                # Handle CLoad instruction and update removed_cycles accordingly
                removed_cycles += self._handle_cload_prune_no_hbm(cinstr, kernel, idx)
            # Check if the CStore variable is an intermediate variable
            elif isinstance(cinstr, cinst.CStore) and cinstr.var_name in self._intermediate_vars and cinstr.var_name in self._xstores_map:
                # Check action for this intermediate variable according to xinst preprocessing
                action = self._xstores_map[cinstr.var_name].action
                if action == InstrAct.KEEP_SPAD:
                    # Reset count, not= longer needed to adjust cycles as cstores are blocking
                    removed_cycles = 0
                    self._last_cq_tp = 0
                else:
                    kernel.cinstrs_map[idx].action = InstrAct.SKIP
                    removed_cycles += ISACInst.CStore.get_throughput()
            elif kernel.cinstrs_map[idx].action != InstrAct.SKIP:
                # Count cycles for other instructions that are not removed
                self._last_cq_tp += get_instruction_tp(cinstr)

            idx += 1  # next instruction

    def _preprocess_cinst_kernel(self, kernel: KernelInfo):
        """
        @brief Preprocesses CInsts in the kernel to build a map of cstores by bundle.

        This method modifies the kernel's fetch_cstores_map in place by mapping each bundle
        to its corresponding ifetch index and list of cstore variable names.

        @param kernel KernelInfo object containing the kernel's CInsts.
        """

        syncm_idx: int = 0  # Sync point with minst
        bundle_idx: int = -1  # Current bundle index
        ifetch_idx: int = -1  # Last ifetch index
        cstore_vars: list[str] = []  # List of cstore variable names in the current bundle

        idx: int = 0
        while idx < len(kernel.cinstrs):
            cinstr = kernel.cinstrs[idx]
            if isinstance(cinstr, cinst.IFetch):
                # Track CStore vars for previous bundle
                kernel.fetch_cstores_map[bundle_idx] = (ifetch_idx, cstore_vars.copy())
                # Start tracking new bundle
                cstore_vars.clear()
                # Update current bundle and ifetch idx
                bundle_idx = cinstr.bundle
                ifetch_idx = idx
            elif isinstance(cinstr, cinst.CExit):
                # Save final bundle's CStore map
                kernel.fetch_cstores_map[bundle_idx] = (ifetch_idx, cstore_vars.copy())
            elif isinstance(cinstr, cinst.CSyncm):
                # Keeping track of the last sync point with minst
                syncm_idx = cinstr.target
            elif GlobalConfig.hasHBM:
                # Find var names from minst instruction by using last sync point and SPAD address
                if isinstance(cinstr, (cinst.BLoad, cinst.BOnes, cinst.CLoad)):
                    minstr_idx = search_minstrs_back(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))
                    cinstr.var_name = kernel.minstrs_map[minstr_idx].minstr.var_name
                elif isinstance(cinstr, cinst.CStore):
                    minstr_idx = search_minstrs_forward(kernel.minstrs_map, syncm_idx, int(cinstr.spad_address))
                    cinstr.var_name = kernel.minstrs_map[minstr_idx].minstr.var_name
                    # Map needed to later match xstores with cstores's var_name
                    cstore_vars.append(cinstr.var_name)
            elif isinstance(cinstr, cinst.CStore):
                # Map needed to later match xstores with cstores's var_name
                cstore_vars.append(cinstr.var_name)

            idx += 1

    def _preprocess_xinst_kernel(self, kernel: KernelInfo, kernel_idx: int):
        """
        @brief Removes unnecessary XInsts from the kernel.
        @param kernel KernelInfo object containing the kernel's XInsts.
        This method modifies the kernel's XInsts in place by removing redundant instructions.
        """

        # Nothing to process if keeping transactions to SPAD
        if self._keep_spad_boundary:
            return

        prev_bundle: int = -1  # Previous bundle index
        xstore_count: int = 0  # Count of XStore instructions in the current bundle

        idx: int = 0
        while idx < len(kernel.xinstrs):
            xinstr = kernel.xinstrs[idx]

            # Reset the xstore counter when a new bundle is encountered
            bundle_idx = xinstr.bundle
            if bundle_idx != prev_bundle:
                prev_bundle = bundle_idx
                xstore_count = 0

            if isinstance(xinstr, xinst.XStore):
                # Extract variable name from CStore map using bundle index and XStore count
                assert bundle_idx in kernel.fetch_cstores_map, f"Bundle {bundle_idx} not found in CStore maps."
                _, cstore_vars = kernel.fetch_cstores_map[bundle_idx]
                var_name = cstore_vars[xstore_count] if xstore_count < len(cstore_vars) else ""

                # Track XStore instructions for intermediate variables
                if var_name in self._intermediate_vars:
                    self._xstores_map[var_name] = XStoreMoveMapEntry(xinstr.source, kernel_idx, (kernel.xinstrs, idx), InstrAct.SKIP)
                    self._var_name_by_reg[xinstr.source] = var_name
                    xstore_count += 1

            elif isinstance(xinstr, xinst.Move):
                # Find variable name from CStore map using bundle index
                fetch_idx, _ = kernel.fetch_cstores_map[bundle_idx]
                var_name = search_cinstrs_back(kernel.cinstrs_map, fetch_idx, xinstr.source)

                # If move for intermediate var and var is tracked
                if var_name in self._intermediate_vars and var_name in self._xstores_map:
                    # If the register was not reused (Still SKIP) no need to send to SPAD
                    if self._xstores_map[var_name].action == InstrAct.SKIP:
                        self._var_name_by_reg.pop(self._xstores_map[var_name].xstore_instr.source)
                        self._xstores_map[var_name].move_instr = (kernel.xinstrs, idx)
                        self._xstores_map[var_name].replace_xstore_with_nop()

                # If tracked register is reused in other move, keep var flushing to SPAD
                if xinstr.dest in self._var_name_by_reg:
                    var_name = self._var_name_by_reg[xinstr.dest]
                    self._xstores_map[var_name].action = InstrAct.KEEP_SPAD
                    self._var_name_by_reg.pop(xinstr.dest)

            # If tracked register is reused in other instruction, keep var flushing to SPAD
            elif isinstance(xinstr, (xinst.Add, xinst.Sub, xinst.Mac, xinst.Maci, xinst.Mul, xinst.Muli, xinst.TwiNTT, xinst.TwNTT)):
                if xinstr.dest in self._var_name_by_reg:
                    var_name = self._var_name_by_reg[xinstr.dest]
                    self._xstores_map[var_name].action = InstrAct.KEEP_SPAD
                    self._var_name_by_reg.pop(xinstr.dest)
            elif isinstance(xinstr, (xinst.NTT, xinst.INTT, xinst.RShuffle)):
                if xinstr.dest0 in self._var_name_by_reg:
                    var_name = self._var_name_by_reg[xinstr.dest0]
                    self._xstores_map[var_name].action = InstrAct.KEEP_SPAD
                    self._var_name_by_reg.pop(xinstr.dest0)
                if xinstr.dest1 in self._var_name_by_reg:
                    var_name = self._var_name_by_reg[xinstr.dest1]
                    self._xstores_map[var_name].action = InstrAct.KEEP_SPAD
                    self._var_name_by_reg.pop(xinstr.dest1)

            idx += 1  # Next instruction

    def preload_kernels(self, kernels_info: list[KernelInfo]):
        """
        @brief Preloads XInsts from all kernels to track XStore instructions.

        This method processes each kernel's XInsts to identify and track XStore
        instructions, which is essential for optimizing the linking process.

        @param kernels_info List of KernelInfo for input kernels.
        """
        for kernel_idx, kernel in enumerate(kernels_info):
            # minst
            if GlobalConfig.hasHBM:
                kernel.minstrs = Loader.load_minst_kernel_from_file(kernel.minst)
                kern_mapper.remap_m_c_instrs_vars(kernel.minstrs, kernel.hbm_remap_dict)

            # cinst
            kernel.cinstrs = Loader.load_cinst_kernel_from_file(kernel.cinst)
            if not GlobalConfig.hasHBM:
                kern_mapper.remap_m_c_instrs_vars(kernel.cinstrs, kernel.hbm_remap_dict)
            else:
                kern_mapper.remap_cinstrs_vars_hbm(kernel.cinstrs, kernel.hbm_remap_dict)
            self._preprocess_cinst_kernel(kernel)

            # xinst
            kernel.xinstrs = Loader.load_xinst_kernel_from_file(kernel.xinst)
            kern_mapper.remap_xinstrs_vars(kernel.xinstrs, kernel.hbm_remap_dict)
            self._preprocess_xinst_kernel(kernel, kernel_idx)

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
        # Process cinsts before linking
        for idx, kernel in enumerate(kernels_info):
            if GlobalConfig.hasHBM:
                self.prune_cinst_kernel_hbm(kernel, kernels_info[idx - 1] if idx > 0 else None)

        self.flush_buffers()

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

                self.link_kernel(kernel)

            if verbose_stream:
                print("[ 100% ] Finalizing output", output_files.prefix, file=verbose_stream)

            self.close()

    def flush_buffers(self):
        """
        @brief Clears internal trackers and resets SPAD offset.
        """
        self._cinst_in_var_tracker.clear()
        self._minst_in_var_tracker.clear()
        self._spad_offset = 0
