from assembler.common.constants import MemoryModel as mmconstants
from assembler.common.decorators import *
from .memory_bank import MemoryBank
from .variable import Variable, findVarByName
from . import mem_utilities as utilities

class HBM(MemoryBank):
    """
    Encapsulates the high-bandwidth DRAM memory model, also known as HBM.

    This class provides methods for managing the allocation and deallocation of variables
    within the HBM, as well as methods for finding available addresses and dumping the
    current state of the HBM.

    Constructors:
        HBM(data_capacity_words: int) -> HBM
            Creates a new HBM object with a specified capacity in words.

        fromCapacityBytes(data_capacity_bytes: int) -> HBM
            Creates an HBM object from a specified capacity in bytes.

    Methods:
        allocateForce(hbm_addr: int, var: Variable)
            Forces the allocation of an existing variable at a specific address.

        deallocate(hbm_addr: int) -> Variable
            Frees up the slot at the specified memory address in the memory buffer.

        deallocateVariable(var: Variable) -> Variable
            Deallocates the specified variable from HBM, freeing up its slot in the memory buffer.

        findAvailableAddress(live_var_names) -> int
            Retrieves the next available HBM address.

        dump(ostream)
            Dumps the current state of the HBM to the specified output stream.
    """

    def __init__(self,
                 hbm_data_capacity_words: int):
        """
        Initializes a new HBM object.

        Args:
            hbm_data_capacity_words (int): Capacity in words for the HBM data region.

        Raises:
            ValueError: If the capacity exceeds the maximum allowed capacity.
        """
        # validate input
        if hbm_data_capacity_words > mmconstants.HBM.MAX_CAPACITY_WORDS:
            raise ValueError(("`hbm_data_capacity_words` must be in the range (0, {}], "
                              "but {} received.".format(mmconstants.HBM.MAX_CAPACITY_WORDS, hbm_data_capacity_words)))

        # initialize base
        super().__init__(hbm_data_capacity_words)

    def allocateForce(self,
                      hbm_addr: int,
                      var: Variable):
        """
        Forces the allocation of an existing variable at a specific address.

        Args:
            hbm_addr (int): Address in HBM where to allocate the variable.
            var (Variable): Variable object to allocate. The variable's hbm_address must be clear (set to a negative value).

        Raises:
            ValueError: If the variable is already allocated or if there is a conflicting allocation.
            RuntimeError: If the HBM is out of capacity.
        """
        # validate variable
        if var.hbm_address >= 0:
            # variable is already allocated (avoid dangling pointers)
            raise ValueError(('`var`: Variable {} address is not cleared. '
                              'Expected negative address, but {} received.'.format(var, var.hbm_address)))

        # allocate in memory bank
        super().allocateForce(hbm_addr, var)
        var.hbm_address = hbm_addr

    def deallocate(self, hbm_addr: int) -> object:
        """
        Frees up the slot at the specified memory address in the memory buffer.

        Args:
            hbm_addr (int): Address of the memory slot to free.

        Raises:
            ValueError: If the address is invalid or already freed.

        Returns:
            Variable: The object that was contained in the deallocated slot.
        """

        # deallocate from memory bank
        var = super().deallocate(hbm_addr)
        var.hbm_address = -1

        return var

    def deallocateVariable(self, var: Variable) -> Variable:
        """
        Deallocates the specified variable from HBM, freeing up its slot in the memory buffer.

        Args:
            var (Variable): Variable to free.

        Raises:
            ValueError: If the variable is not allocated in HBM.

        Returns:
            Variable: The object that was contained in the deallocated slot.
        """
        retval = self.deallocate(var.hbm_address)
        assert(retval.name == var.name)
        return retval

    def findAvailableAddress(self,
                             live_var_names) -> int:
        """
        Retrieves the next available HBM address.

        Args:
            live_var_names (set or list): A collection of variable names that should not be removed from HBM.

        Returns:
            int: The first empty address, or -1 if no suitable address is found.
        """
        return utilities.findAvailableLocation(self.buffer, live_var_names)

    def dump(self, ostream):
        """
        Dumps the current state of the HBM to the specified output stream.

        Args:
            ostream: The output stream to write the HBM state to.
        """
        print('HBM', file = ostream)
        print(f'Max Capacity, {self.CAPACITY}, Bytes', file = ostream)
        print(f'Max Capacity, {self.CAPACITY_WORDS}, Words', file = ostream)
        print(f'Current Capacity, {self.currentCapacityWords}, Words', file = ostream)
        print(f'Current Occupied, {self.CAPACITY_WORDS - self.currentCapacityWords}, Words', file = ostream)
        print("", file = ostream)
        print("address, variable, variable hbm", file = ostream)
        last_addr = 0
        for addr, variable in enumerate(self.buffer):
            if variable is not None:
                for idx in range(last_addr, addr):
                    # empty addresses
                    print(f'{idx}, None', file = ostream)
                if variable.name:
                    print('{}, {}'.format(addr,
                                          variable.name,
                                          variable.hbm_address),
                          file = ostream)
                else:
                    print('f{addr}, Dummy_{variable.tag}',
                          file = ostream)
                last_addr = addr + 1
