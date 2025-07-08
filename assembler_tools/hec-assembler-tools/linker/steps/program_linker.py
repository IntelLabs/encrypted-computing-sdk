# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief This module provides functionality to link kernels into a program."""

from typing import Dict, Any, cast
from linker import MemoryModel
from linker.instructions import minst, cinst, dinst
from linker.instructions.dinst.dinstruction import DInstruction
from assembler.common.config import GlobalConfig
from assembler.instructions import cinst as ISACInst


class LinkedProgram:  # pylint: disable=too-many-instance-attributes
    """
    @class LinkedProgram
    @brief Encapsulates a linked program.

    This class offers facilities to track and link kernels, and
    outputs the linked program to specified output streams as kernels
    are linked.

    The program itself is not contained in this object.
    """

    def __init__(
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
        self._kernel_count = 0  # Number of kernels linked into this program
        self._is_open = (
            True  # Tracks whether this program is still accepting kernels to link
        )

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
            f"{cexit_cinstr.tokens[0]}, {cexit_cinstr.to_line()}",
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
            f"{cmsyncc_minstr.tokens[0]}, {cmsyncc_minstr.to_line()}",
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
        if hbm_address < 0:
            raise RuntimeError(
                f'Invalid negative HBM address for variable "{var_name}".'
            )
        if var_name in self.__mem_model.mem_info_vars:
            # Cast to dictionary to fix the indexing error
            mem_info_vars_dict = cast(Dict[str, Any], self.__mem_model.mem_info_vars)
            if mem_info_vars_dict[var_name].hbm_address != hbm_address:
                raise RuntimeError(
                    (
                        f"Declared HBM address "
                        f"({mem_info_vars_dict[var_name].hbm_address})"
                        f" of mem Variable '{var_name}'"
                        f" differs from allocated HBM address ({hbm_address})."
                    )
                )

    def _validate_spad_address(self, var_name: str, spad_address: int):
        """
        @brief Validates the SPAD address for a variable (only available when no HBM).

        @param var_name The name of the variable.
        @param spad_address The SPAD address to validate.

        @exception RuntimeError If the SPAD address is invalid or does not match the declared address.
        """
        # only available when no HBM
        assert not GlobalConfig.hasHBM

        # this method will validate the variable SPAD address against the
        # original HBM address, since there is no HBM
        if spad_address < 0:
            raise RuntimeError(
                f'Invalid negative SPAD address for variable "{var_name}".'
            )
        if var_name in self.__mem_model.mem_info_vars:
            # Cast to dictionary to fix the indexing error
            mem_info_vars_dict = cast(Dict[str, Any], self.__mem_model.mem_info_vars)
            if mem_info_vars_dict[var_name].hbm_address != spad_address:
                raise RuntimeError(
                    (
                        f"Declared HBM address"
                        f" ({mem_info_vars_dict[var_name].hbm_address})"
                        f" of mem Variable '{var_name}'"
                        f" differs from allocated HBM address ({spad_address})."
                    )
                )

    def _update_minsts(self, kernel_minstrs: list):
        """
        @brief Updates the MInsts in the kernel to offset to the current expected
        synchronization points, and convert variable placeholders/names into
        the corresponding HBM address.

        All MInsts in the kernel are expected to synchronize with CInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel_minstrs List of MInstructions to update.
        """
        for minstr in kernel_minstrs:
            # Update msyncc
            if isinstance(minstr, minst.MSyncc):
                minstr.target = minstr.target + self._cinst_line_offset
            # Change mload variable names into HBM addresses
            if isinstance(minstr, minst.MLoad):
                var_name = minstr.source
                hbm_address = self.__mem_model.use_variable(
                    var_name, self._kernel_count
                )
                self._validate_hbm_address(var_name, hbm_address)
                minstr.source = str(hbm_address)
                minstr.comment = (
                    f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}"
                    if minstr.comment
                    else ""
                )
            # Change mstore variable names into HBM addresses
            if isinstance(minstr, minst.MStore):
                var_name = minstr.dest
                hbm_address = self.__mem_model.use_variable(
                    var_name, self._kernel_count
                )
                self._validate_hbm_address(var_name, hbm_address)
                minstr.dest = str(hbm_address)
                minstr.comment = (
                    f" var: {var_name} - HBM({hbm_address})" + f";{minstr.comment}"
                    if minstr.comment
                    else ""
                )

    def _remove_and_merge_csyncm_cnop(self, kernel_cinstrs: list):
        """
        @brief Remove csyncm instructions and merge consecutive cnop instructions.

        @param kernel_cinstrs List of CInstructions to process.
        """
        i = 0
        current_bundle = 0
        csyncm_count = 0
        while i < len(kernel_cinstrs):
            cinstr = kernel_cinstrs[i]
            cinstr.tokens[0] = str(i)  # Update the line number

            # ------------------------------
            # This code block will remove csyncm instructions and keep track,
            # later adding their throughput into a cnop instruction before
            # a new bundle is fetched.

            if isinstance(cinstr, cinst.CNop):
                # Add the missing cycles to any cnop we encounter up to this point
                cinstr.cycles += csyncm_count * ISACInst.CSyncm.get_throughput()
                # Idle cycles to account for the csyncm have been added
                csyncm_count = 0

            if isinstance(cinstr, (cinst.IFetch, cinst.NLoad, cinst.BLoad)):
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
                    kernel_cinstrs.insert(i, cinstr_nop)
                    csyncm_count = 0
                    i += 1
                if isinstance(cinstr, cinst.IFetch):
                    current_bundle = cinstr.bundle + 1
                    # Update the line number
                    cinstr.tokens[0] = i

            if isinstance(cinstr, cinst.CSyncm):
                # Remove instruction
                kernel_cinstrs.pop(i)
                if current_bundle > 0:
                    csyncm_count += 1
            else:
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
            #         cinstr_nop = cinst.CNop([i, cinst.CNop.name, str(ISACInst.CSyncm.get_throughput())]) # Subtract 1 because cnop n, waits for n+1 cycles
            #         kernel_cinstrs.insert(i, cinstr_nop)
            #
            # i += 1 # next instruction

        # Merge continuous cnop
        i = 0
        while i < len(kernel_cinstrs):
            cinstr = kernel_cinstrs[i]
            cinstr.tokens[0] = str(i)
            if isinstance(cinstr, cinst.CNop):
                # Do look ahead
                if i + 1 < len(kernel_cinstrs):
                    if isinstance(kernel_cinstrs[i + 1], cinst.CNop):
                        # Add 1 because cnop n, waits for n+1 cycles
                        kernel_cinstrs[i + 1].cycles += cinstr.cycles + 1
                        kernel_cinstrs.pop(i)
                        i -= 1
            i += 1

    def _update_cinsts_addresses_and_offsets(self, kernel_cinstrs: list):
        """
        @brief Updates bundle/target offsets and variable names to addresses for CInsts.

        All CInsts in the kernel are expected to start at bundle 0, and to
        synchronize with MInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel_cinstrs List of CInstructions to update.
        """
        for cinstr in kernel_cinstrs:
            # Update ifetch
            if isinstance(cinstr, cinst.IFetch):
                cinstr.bundle = cinstr.bundle + self._bundle_offset
            # Update xinstfetch
            if isinstance(cinstr, cinst.XInstFetch):
                raise NotImplementedError(
                    "`xinstfetch` not currently supported by linker."
                )
            # Update csyncm
            if isinstance(cinstr, cinst.CSyncm):
                cinstr.target = cinstr.target + self._minst_line_offset

            if not GlobalConfig.hasHBM:
                # update all SPAD instruction variable names to be SPAD addresses
                # change xload variable names into SPAD addresses
                if isinstance(
                    cinstr, (cinst.BLoad, cinst.BOnes, cinst.CLoad, cinst.NLoad)
                ):
                    var_name = cinstr.source
                    hbm_address = self.__mem_model.use_variable(
                        var_name, self._kernel_count
                    )
                    self._validate_spad_address(var_name, hbm_address)
                    cinstr.source = str(hbm_address)
                    cinstr.comment = (
                        f" var: {var_name} - HBM({hbm_address})" + f";{cinstr.comment}"
                        if cinstr.comment
                        else ""
                    )
                if isinstance(cinstr, cinst.CStore):
                    var_name = cinstr.dest
                    hbm_address = self.__mem_model.use_variable(
                        var_name, self._kernel_count
                    )
                    self._validate_spad_address(var_name, hbm_address)
                    cinstr.dest = str(hbm_address)
                    cinstr.comment = (
                        f" var: {var_name} - HBM({hbm_address})" + f";{cinstr.comment}"
                        if cinstr.comment
                        else ""
                    )

    def _update_cinsts(self, kernel_cinstrs: list):
        """
        @brief Updates the CInsts in the kernel to offset to the current expected bundle
        and synchronization points.

        All CInsts in the kernel are expected to start at bundle 0, and to
        synchronize with MInsts starting at line 0.
        Does not change the LinkedProgram object.

        @param kernel_cinstrs List of CInstructions to update.
        """
        if not GlobalConfig.hasHBM:
            self._remove_and_merge_csyncm_cnop(kernel_cinstrs)

        self._update_cinsts_addresses_and_offsets(kernel_cinstrs)

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
                raise RuntimeError(
                    f'Detected invalid bundle. Instruction bundle is less than previous: "{xinstr.to_line()}"'
                )
            last_bundle = xinstr.bundle
        return last_bundle

    def link_kernel(
        self, kernel_minstrs: list, kernel_cinstrs: list, kernel_xinstrs: list
    ):
        """
        @brief Links a specified kernel (given by its three instruction queues) into this
        program.

        The adjusted kernels will be appended into the output streams specified during
        construction of this object.

        @param kernel_minstrs List of MInstructions for the MInst Queue corresponding to the kernel to link.
            These instructions will be modified by this method.
        @param kernel_cinstrs List of CInstructions for the CInst Queue corresponding to the kernel to link.
            These instructions will be modified by this method.
        @param kernel_xinstrs List of XInstructions for the XInst Queue corresponding to the kernel to link.
            These instructions will be modified by this method.

        @exception RuntimeError If the program is closed and does not accept new kernels.
        """
        if not self.is_open:
            raise RuntimeError("Program is closed and does not accept new kernels.")

        # No minsts without HBM
        if not GlobalConfig.hasHBM:
            kernel_minstrs = []

        self._update_minsts(kernel_minstrs)
        self._update_cinsts(kernel_cinstrs)
        self._bundle_offset = self._update_xinsts(kernel_xinstrs) + 1

        # Append the kernel to the output

        for xinstr in kernel_xinstrs:
            print(xinstr.to_line(), end="", file=self._xinst_ostream)
            if not GlobalConfig.suppress_comments and xinstr.comment:
                print(f" #{xinstr.comment}", end="", file=self._xinst_ostream)
            print(file=self._xinst_ostream)

        for idx, cinstr in enumerate(kernel_cinstrs[:-1]):  # Skip the `cexit`
            line_no = idx + self._cinst_line_offset
            print(f"{line_no}, {cinstr.to_line()}", end="", file=self._cinst_ostream)
            if not GlobalConfig.suppress_comments and cinstr.comment:
                print(f" #{cinstr.comment}", end="", file=self._cinst_ostream)
            print(file=self._cinst_ostream)

        for idx, minstr in enumerate(kernel_minstrs[:-1]):  # Skip the exit `msyncc`
            line_no = idx + self._minst_line_offset
            print(f"{line_no}, {minstr.to_line()}", end="", file=self._minst_ostream)
            if not GlobalConfig.suppress_comments and minstr.comment:
                print(f" #{minstr.comment}", end="", file=self._minst_ostream)
            print(file=self._minst_ostream)

        self._minst_line_offset += (
            len(kernel_minstrs) - 1
        )  # Subtract last line that is getting removed
        self._cinst_line_offset += (
            len(kernel_cinstrs) - 1
        )  # Subtract last line that is getting removed
        self._kernel_count += 1  # Count the appended kernel

    @classmethod
    def join_dinst_kernels(
        cls, kernels_instrs: list[list[DInstruction]]
    ) -> list[DInstruction]:
        """
        @brief Joins a list of dinst kernels, consolidating variables that are outputs in one kernel
        and inputs in the next. This ensures that variables carried across kernels are not duplicated,
        and their Mem addresses are consistent.

        @param kernels_instrs List of Kernels' DInstructions lists.

        @return list[DInstruction] A new instruction list representing the concatenated memory info.

        @exception ValueError If no DInstructions lists are provided for concatenation.
        """

        if not kernels_instrs:
            raise ValueError("No DInstructions lists provided for concatenation.")

        # Use dictionaries to track unique variables by name
        inputs: dict[str, DInstruction] = {}
        carry_over_vars: dict[str, DInstruction] = {}

        mem_address: int = 0
        new_kernels_instrs: list[DInstruction] = []
        for kernel_instrs in kernels_instrs:
            for cur_dinst in kernel_instrs:

                # Save the current output instruction to add at the end
                if isinstance(cur_dinst, dinst.DStore):
                    key = cur_dinst.var
                    carry_over_vars[key] = cur_dinst
                    continue

                if isinstance(cur_dinst, (dinst.DLoad, dinst.DKeyGen)):
                    key = cur_dinst.var
                    # Skip if the input is already in carry-over from previous outputs
                    if key in carry_over_vars:
                        carry_over_vars.pop(
                            key
                        )  # Remove from (output) carry-overs since it's now an input
                        continue

                    # If the input is not (a previous output) in carry-over, add if it's not already (loaded) in inputs
                    if key not in inputs:
                        inputs[key] = cur_dinst
                        cur_dinst.address = mem_address
                        mem_address = mem_address + 1

                        new_kernels_instrs.append(cur_dinst)
                        continue

        # Add remaining carry-over variables to the new instructions
        for _, var in carry_over_vars.items():
            var.address = mem_address
            new_kernels_instrs.append(var)
            mem_address = mem_address + 1

        return new_kernels_instrs
