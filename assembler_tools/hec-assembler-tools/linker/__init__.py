# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief linker/__init__.py contains classes to encapsulate the memory model used by the linker."""

import collections.abc as collections

from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info


class VariableInfo(mem_info.MemInfoVariable):
    """
    @brief Represents information about a variable in the memory model.
    """

    def __init__(self, var_name, hbm_address=-1):
        """
        @brief Initializes a VariableInfo object.

        @param var_name The name of the variable.
        @param hbm_address The HBM address of the variable. Defaults to -1.
        """
        super().__init__(var_name, hbm_address)
        self.uses = 0
        self.last_kernel_used = -1


class HBM:
    """
    @brief Represents the HBM model.
    """

    def __init__(self, hbm_size_words: int):
        """
        @brief Initializes an HBM object.

        @param hbm_size_words The size of the HBM in words.
        @throws ValueError If hbm_size_words is less than 1.
        """
        if hbm_size_words < 1:
            raise ValueError("`hbm_size_words` must be a positive integer.")
        # Represents the memory buffer where variables live
        self.__buffer = [None] * hbm_size_words

    @property
    def capacity(self) -> int:
        """
        @brief Gets the capacity in words for the HBM buffer.

        @return The capacity of the HBM buffer.
        """
        return len(self.buffer)

    @property
    def buffer(self) -> list:
        """
        @brief Gets the HBM buffer.

        @return The HBM buffer.
        """
        return self.__buffer

    def force_allocate(self, var_info: VariableInfo, hbm_address: int):
        """
        @brief Forcefully allocates a variable at a specific HBM address.

        @param var_info The variable information.
        @param hbm_address The HBM address to allocate the variable.
        @throws IndexError If hbm_address is out of bounds.
        @throws ValueError If the variable is already allocated at a different address.
        @throws RuntimeError If the HBM address is already occupied by another variable.
        """
        if hbm_address < 0 or hbm_address >= len(self.buffer):
            raise IndexError(
                f"`hbm_address` out of bounds. Expected a word address in range [0, {len(self.buffer)}), but {hbm_address} received"
            )
        if var_info.hbm_address != hbm_address:
            if var_info.hbm_address >= 0:
                raise ValueError(f"`var_info`: variable {var_info.var_name} already allocated in address {var_info.hbm_address}.")

            in_var_info = self.buffer[hbm_address]
            # Validate hbm address
            if not GlobalConfig.hasHBM:
                # Attempt to recycle SPAD locations inside kernel when no HBM
                # Note: there is no HBM, so, SPAD is used as the sole memory space
                if in_var_info and in_var_info.uses > 0:
                    raise RuntimeError(
                        f"HBM address {hbm_address} already occupied by variable {in_var_info.var_name} "
                        f"when attempting to allocate variable {var_info.var_name}"
                    )
            else:
                if in_var_info and (in_var_info.uses > 0 or in_var_info.last_kernel_used >= var_info.last_kernel_used):
                    raise RuntimeError(
                        f"HBM address {hbm_address} already occupied by variable {in_var_info.var_name} "
                        f"when attempting to allocate variable {var_info.var_name}"
                    )
            var_info.hbm_address = hbm_address
            self.buffer[hbm_address] = var_info

    def allocate(self, var_info: VariableInfo):
        """
        @brief Allocates a variable in the HBM.

        @param var_info The variable information.
        @throws RuntimeError If there is no available HBM memory.
        """
        # Find next available HBM address
        retval = -1
        for idx, in_var_info in enumerate(self.buffer):
            if not GlobalConfig.hasHBM:
                # Attempt to recycle SPAD locations inside kernel when no HBM
                # Note: there is no HBM, so, SPAD is used as the sole memory space
                if not in_var_info or in_var_info.uses <= 0:
                    retval = idx
                    break
            else:
                if not in_var_info or (in_var_info.uses <= 0 and in_var_info.last_kernel_used < var_info.last_kernel_used):
                    retval = idx
                    break
        if retval < 0:
            raise RuntimeError("Out of HBM memory.")
        self.force_allocate(var_info, retval)


class MemoryModel:
    """
    @brief Encapsulates the memory model for a linker run, tracking HBM usage and program variables.
    """

    def __init__(self, hbm_size_words: int, mem_meta_info: mem_info.MemInfo):
        """
        @brief Initializes a MemoryModel object.

        @param hbm_size_words The size of the HBM in words.
        @param mem_meta_info The memory metadata information.
        """
        self.hbm = HBM(hbm_size_words)
        self.__mem_info = mem_meta_info
        self.__variables: dict[str, VariableInfo] = {}  # dict(var_name: str, VariableInfo)

        # Group related collections into a dictionary
        self.__mem_collections = {
            "keygen_vars": {var_info.var_name: var_info for var_info in self.__mem_info.keygens},
            "inputs": {var_info.var_name: var_info for var_info in self.__mem_info.inputs},
            "outputs": {var_info.var_name: var_info for var_info in self.__mem_info.outputs},
            "meta": (
                {var_info.var_name: var_info for var_info in self.__mem_info.metadata.intt_auxiliary_table}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.intt_routing_table}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ntt_auxiliary_table}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ntt_routing_table}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ones}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.twiddle}
                | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.keygen_seeds}
            ),
        }

        # Derived collections
        self.__mem_info_fixed_addr_vars = self.__mem_collections["outputs"] | self.__mem_collections["meta"]
        # Keygen variables should not be part of mem_info_vars set since they
        # do not start in HBM
        self.__mem_info_vars = self.__mem_collections["inputs"] | self.__mem_collections["outputs"] | self.__mem_collections["meta"]

    @property
    def mem_info_meta(self) -> collections.Collection:
        """
        @brief Set of metadata variable names in MemInfo used to construct this object.

        Clients must not modify this set.

        @return Collection of metadata variable names.
        """
        return self.__mem_collections["meta"]

    @property
    def mem_info_vars(self) -> collections.Collection:
        """
        @brief Gets the set of variable names in MemInfo used to construct this object.

        @return The set of variable names.
        """
        return self.__mem_info_vars

    @property
    def variables(self) -> dict:
        """
        @brief Gets direct access to internal variables dictionary.

        Clients should use as read-only. Must not add, replace, remove or change
        contents in any way. Use provided helper functions to manipulate.

        @return A dictionary of variables.
        """
        return self.__variables

    def add_variable(self, var_name: str):
        """
        @brief Adds a variable to the HBM model.

        If variable already exists, its `uses` field is incremented.

        @param var_name The name of the variable to add.
        """
        var_info: VariableInfo
        if var_name in self.variables:
            var_info = self.variables[var_name]
        else:
            var_info = VariableInfo(var_name)
            if var_name in self.__mem_info_vars:
                # Variables explicitly marked in mem file must persist throughout the program
                # with predefined HBM address
                if var_name in self.__mem_info_fixed_addr_vars:
                    var_info.uses = float("inf")
                else:
                    var_info.uses = 0
                self.hbm.force_allocate(var_info, self.__mem_info_vars[var_name].hbm_address)
            else:
                # Variables not explicitly marked in mem file are allocated on demand
                var_info.hbm_address = -1
            self.variables[var_name] = var_info

        var_info.uses += 1

    def use_variable(self, var_name: str, kernel: int) -> int:
        """
        @brief Uses a variable, decrementing its usage count.

        If a variable usage count reaches zero, it will be deallocated from HBM, if needed,
        when a future kernel requires HBM space.

        @param var_name The name of the variable to use.
        @param kernel The kernel that is using the variable.
        @return The HBM address for the variable.
        """
        var_info: VariableInfo = self.variables[var_name]
        assert var_info.uses > 0

        var_info.uses -= 1  # Mark the usage
        var_info.last_kernel_used = kernel
        if var_info.hbm_address < 0:
            # Find HBM address for variable
            self.hbm.allocate(var_info)

        assert var_info.hbm_address >= 0
        assert self.hbm.buffer[var_info.hbm_address].var_name == var_info.var_name, (
            f"Expected variable {var_info.var_name} in HBM {var_info.hbm_address},"
            f" but variable {self.hbm.buffer[var_info.hbm_address].var_name} found instead."
        )

        return var_info.hbm_address
