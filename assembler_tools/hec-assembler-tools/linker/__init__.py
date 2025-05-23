import collections.abc as collections
from assembler.common.config import GlobalConfig
from assembler.memory_model import mem_info

# linker/__init__.py contains classes to encapsulate the memory model used
# by the linker.

class VariableInfo(mem_info.MemInfoVariable):
    """
    Represents information about a variable in the memory model.
    """

    def __init__(self, var_name, hbm_address=-1):
        """
        Initializes a VariableInfo object.

        Parameters:
            var_name (str): The name of the variable.
            hbm_address (int): The HBM address of the variable. Defaults to -1.
        """
        super().__init__(var_name, hbm_address)
        self.uses = 0
        self.last_kernel_used = -1

class HBM:
    """
    Represents the HBM model.
    """

    def __init__(self, hbm_size_words: int):
        """
        Initializes an HBM object.

        Parameters:
            hbm_size_words (int): The size of the HBM in words.

        Raises:
            ValueError: If hbm_size_words is less than 1.
        """
        if hbm_size_words < 1:
            raise ValueError('`hbm_size_words` must be a positive integer.')
        # Represents the memory buffer where variables live
        self.__buffer = [None] * hbm_size_words

    @property
    def capacity(self) -> int:
        """
        Gets the capacity in words for the HBM buffer.

        Returns:
            int: The capacity of the HBM buffer.
        """
        return len(self.buffer)

    @property
    def buffer(self) -> list:
        """
        Gets the HBM buffer.

        Returns:
            list: The HBM buffer.
        """
        return self.__buffer

    def forceAllocate(self, var_info: VariableInfo, hbm_address: int):
        """
        Forcefully allocates a variable at a specific HBM address.

        Parameters:
            var_info (VariableInfo): The variable information.
            hbm_address (int): The HBM address to allocate the variable.

        Raises:
            IndexError: If hbm_address is out of bounds.
            ValueError: If the variable is already allocated at a different address.
            RuntimeError: If the HBM address is already occupied by another variable.
        """
        if hbm_address < 0 or hbm_address >= len(self.buffer):
            raise IndexError('`hbm_address` out of bounds. Expected a word address in range [0, {}), but {} received'.format(len(self.buffer),
                                                                                                                             hbm_address))
        if var_info.hbm_address != hbm_address:
            if var_info.hbm_address >= 0:
                raise ValueError(f'`var_info`: variable {var_info.var_name} already allocated in address {var_info.hbm_address}.')

            in_var_info = self.buffer[hbm_address]
            # Validate hbm address
            if not GlobalConfig.hasHBM:
                # Attempt to recycle SPAD locations inside kernel when no HBM
                # Note: there is no HBM, so, SPAD is used as the sole memory space
                if in_var_info and in_var_info.uses > 0:
                    raise RuntimeError(('HBM address {} already occupied by variable {} '
                                        'when attempting to allocate variable {}').format(hbm_address,
                                                                                          in_var_info.var_name,
                                                                                          var_info.var_name))
            else:
                if in_var_info \
                and (in_var_info.uses > 0 or in_var_info.last_kernel_used >= var_info.last_kernel_used):
                    raise RuntimeError(('HBM address {} already occupied by variable {} '
                                        'when attempting to allocate variable {}').format(hbm_address,
                                                                                        in_var_info.var_name,
                                                                                        var_info.var_name))
            var_info.hbm_address = hbm_address
            self.buffer[hbm_address] = var_info

    def allocate(self, var_info: VariableInfo):
        """
        Allocates a variable in the HBM.

        Parameters:
            var_info (VariableInfo): The variable information.

        Raises:
            RuntimeError: If there is no available HBM memory.
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
                if not in_var_info \
                or (in_var_info.uses <= 0 and in_var_info.last_kernel_used < var_info.last_kernel_used):
                    retval = idx
                    break
        if retval < 0:
            raise RuntimeError('Out of HBM memory.')
        self.forceAllocate(var_info, retval)

class MemoryModel:
    """
    Encapsulates the memory model for a linker run, tracking HBM usage and program variables.
    """

    def __init__(self, hbm_size_words: int, mem_meta_info: mem_info.MemInfo):
        """
        Initializes a MemoryModel object.

        Parameters:
            hbm_size_words (int): The size of the HBM in words.
            mem_meta_info (mem_info.MemInfo): The memory metadata information.
        """
        self.hbm = HBM(hbm_size_words)
        self.__mem_info = mem_meta_info
        self.__variables = {}  # dict(var_name: str, VariableInfo)
        self.__keygen_vars = {var_info.var_name: var_info for var_info in self.__mem_info.keygens}
        self.__mem_info_inputs = {var_info.var_name: var_info for var_info in self.__mem_info.inputs}
        self.__mem_info_outputs = {var_info.var_name: var_info for var_info in self.__mem_info.outputs}
        self.__mem_info_meta = {var_info.var_name: var_info for var_info in self.__mem_info.metadata.intt_auxiliary_table} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.intt_routing_table} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ntt_auxiliary_table} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ntt_routing_table} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.ones} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.twiddle} \
                             | {var_info.var_name: var_info for var_info in self.__mem_info.metadata.keygen_seeds}
        self.__mem_info_fixed_addr_vars = self.__mem_info_outputs | self.__mem_info_meta
        # Keygen variables should not be part of mem_info_vars set since they
        # do not start in HBM
        self.__mem_info_vars = self.__mem_info_inputs | self.__mem_info_outputs | self.__mem_info_meta

    @property
    def mem_info_meta(self) -> collections.Collection:
        """
        Set of metadata variable names in MemInfo used to construct this object.
        Clients must not modify this set.
        """
        return self.__mem_info_meta
    
    @property
    def mem_info_vars(self) -> collections.Collection:
        """
        Gets the set of variable names in MemInfo used to construct this object.

        Returns:
            collections.Collection: The set of variable names.
        """
        return self.__mem_info_vars

    @property
    def variables(self) -> dict:
        """
        Gets direct access to internal variables dictionary.

        Clients should use as read-only. Must not add, replace, remove or change
        contents in any way. Use provided helper functions to manipulate.

        Returns:
            dict: A dictionary of variables.
        """
        return self.__variables

    def addVariable(self, var_name: str):
        """
        Adds a variable to the HBM model. If variable already exists, its `uses`
        field is incremented.

        Parameters:
            var_name (str): The name of the variable to add.
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
                    var_info.uses = float('inf')
                self.hbm.forceAllocate(var_info,
                                       self.__mem_info_vars[var_name].hbm_address)
            self.variables[var_name] = var_info
        var_info.uses += 1

    def useVariable(self, var_name: str, kernel: int) -> int:
        """
        Uses a variable, decrementing its usage count.

        If a variable usage count reaches zero, it will be deallocated from HBM, if needed,
        when a future kernel requires HBM space.

        Parameters:
            var_name (str): The name of the variable to use.
            kernel (int): The kernel that is using the variable.

        Returns:
            int: The HBM address for the variable.
        """
        var_info: VariableInfo = self.variables[var_name]
        assert var_info.uses > 0

        var_info.uses -= 1  # Mark the usage
        var_info.last_kernel_used = kernel

        if var_info.hbm_address < 0:
            # Find HBM address for variable
            self.hbm.allocate(var_info)

        assert var_info.hbm_address >= 0
        assert self.hbm.buffer[var_info.hbm_address].var_name == var_info.var_name, \
            f'Expected variable {var_info.var_name} in HBM {var_info.hbm_address}, but variable {self.hbm[var_info.hbm_address].var_name} found instead.'

        return var_info.hbm_address