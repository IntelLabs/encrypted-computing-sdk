import itertools

from assembler.common.constants import MemoryModel as mmconstants
from assembler.common.counter import Counter
from assembler.common.decorators import *
from .memory_bank import MemoryBank
from .variable import Variable
from . import mem_utilities as utilities

class SPAD(MemoryBank):
    """
    Encapsulates the SRAM cache, also known as SPAD, within the memory model.

    This class provides methods for managing the allocation and deallocation of variables
    within the SPAD, as well as methods for tracking access and finding available addresses.

    Constructors:
        SPAD(data_capacity_words: int) -> SPAD
            Creates a new SPAD object with a specified capacity in words.

        fromCapacityBytes(data_capacity_bytes: int) -> SPAD
            Creates a SPAD object from a specified capacity in bytes.

    Properties:
        buffer (list): Inherited property that returns the SPAD's buffer, allocated to hold up to
        CAPACITY_WORDS `Variable` objects.

    Methods:
        allocateForce(addr: int, variable: Variable)
            Forces the allocation of an existing `Variable` object at a specific address.

        deallocate(addr: int) -> Variable
            Frees up the slot at the specified memory address in the memory buffer.

        findAvailableAddress(live_var_names: set or list, replacement_policy: str = None) -> int
            Retrieves the next available SPAD address or proposes an address to use if all are
            occupied, based on a replacement policy.
    """

    class AccessTracker:
        """
        Tracks access to SPAD addresses by various instructions.

        This class maintains a count and the last access instruction for each type of access,
        allowing clients to determine the order of accesses.
        """

        __idx_counter = Counter.count(0) # internal unique sequence counter to generate monotonous indices

        def __init__(self,
                     last_mload = None,
                     last_mstore = None,
                     last_cload = None,
                     last_cstore = None):
            self.__last_mload = (next(SPAD.AccessTracker.__idx_counter), last_mload)
            self.__last_mstore = (next(SPAD.AccessTracker.__idx_counter), last_mstore)
            self.__last_cload = (next(SPAD.AccessTracker.__idx_counter), last_cload)
            self.__last_cstore = (next(SPAD.AccessTracker.__idx_counter), last_cstore)

        @property
        def last_mload(self) -> tuple:
            """
            Retrieves the last `mload` access.

            Retrieved tuple contains:
                count - a count number that can be used to compare with other accesses in this object.
                    This value monotonically increases with each access regardless of access type. It
                    can be used to identify which access occurred first when two accesses are needed.
                minstr - the last `mload` instruction to access, or None, if no last access.

            Returns:
                tuple: A tuple containing a count and the last `mload` instruction.
            """
            return self.__last_mload

        @last_mload.setter
        def last_mload(self, value: object):
            self.__last_mload = (next(SPAD.AccessTracker.__idx_counter), value)

        @property
        def last_mstore(self) -> tuple:
            """
            Gets the last `mstore` access.

            Returns:
                tuple: A tuple containing a count and the last `mstore` instruction.
            """
            return self.__last_mstore

        @last_mstore.setter
        def last_mstore(self, value: object):
            self.__last_mstore = (next(SPAD.AccessTracker.__idx_counter), value)

        @property
        def last_cload(self) -> tuple:
            """
            Gets the last `cload` access.

            Returns:
                tuple: A tuple containing a count and the last `cload` instruction.
            """
            return self.__last_cload

        @last_cload.setter
        def last_cload(self, value: object):
            self.__last_cload = (next(SPAD.AccessTracker.__idx_counter), value)

        @property
        def last_cstore(self) -> tuple:
            """
            Gets the last `cstore` access.

            Returns:
                tuple: A tuple containing a count and the last `cstore` instruction.
            """
            return self.__last_cstore

        @last_cstore.setter
        def last_cstore(self, value: object):
            self.__last_cstore = (next(SPAD.AccessTracker.__idx_counter), value)

    # Constructor
    # -----------

    def __init__(self,
                 data_capacity_words: int):
        """
        Initializes a new SPAD object representing the SRAM cache or scratchpad.

        Args:
            data_capacity_words (int): Capacity in words for the SPAD.

        Raises:
            ValueError: If the capacity exceeds the maximum allowed capacity.
        """
        # validate input
        if data_capacity_words > mmconstants.SPAD.MAX_CAPACITY_WORDS:
            raise ValueError(("`data_capacity_words` must be in the range (0, {}], "
                              "but {} received.").format(mmconstants.SPAD.MAX_CAPACITY_WORDS, data_capacity_words))

        # initialize base
        super().__init__(data_capacity_words)
        self.__var_lookup = {} # dict(var_name: str, variable: Variable) - reverse look-up on variable name
        self.__access_tracker = [ SPAD.AccessTracker() for _ in range(len(self.buffer)) ]

    # Special methods
    # ---------------

    def __contains__(self, var_name):
        """
        Checks if a variable name is contained within the SPAD.

        Args:
            var_name (str or Variable): The variable name or Variable object to check.

        Returns:
            bool: True if the variable is contained within the SPAD, False otherwise.
        """
        return self._contains(var_name.name) if isinstance(var_name, Variable) else self._contains(var_name)

    def __getitem__(self, key):
        """
        Retrieves a contained Variable object by name or index.

        Args:
            key (str or int): The variable name or index to retrieve.

        Returns:
            Variable: The contained Variable object, or None if not found.
        """
        return self.findContainedVariable(key) if isinstance(key, str) else self.buffer[key]

    # Methods and properties
    # ----------------------

    def getAccessTracking(self, spad_address: int) -> AccessTracker:
        """
        Gets the access tracker object for the specified SPAD address.

        This is used to track last access to specified SPAD address by CInstructions
        and MInstructions. See `AccessTracker` for tracking information.

        Clients can either use the returned object to query for last access or
        to specify a new last access.

        Args:
            spad_address (int): SPAD address for which access tracking is requested.

        Returns:
            AccessTracker: A mutable AccessTracker object containing the last access instructions.

        Raises:
            IndexError: If the SPAD address is out of range.
        """
        if spad_address < 0 or spad_address >= len(self.__access_tracker):
            raise IndexError("`spad_address` out of range.")
        return self.__access_tracker[spad_address]

    def _contains(self, var_name) -> bool:
        """
        Checks if a variable name is contained within the SPAD.

        Args:
            var_name (str): The variable name to check.

        Returns:
            bool: True if the variable is contained within the SPAD, False otherwise.
        """
        return var_name in self.__var_lookup

    def findContainedVariable(self, var_name: str) -> Variable:
        """
        Retrieves a contained Variable object by name.

        Args:
            var_name (str): The name of the variable to retrieve.

        Returns:
            Variable: The contained Variable object, or None if not found.
        """
        return self.__var_lookup[var_name] if var_name in self.__var_lookup else None

    def allocateForce(self,
                      addr: int,
                      variable: Variable):
        """
        Forces the allocation of an existing `Variable` object at a specific address.

        Args:
            addr (int): Address in SPAD where to allocate the `Variable` object.
            variable (Variable): Variable object to allocate. The variable's spad_address must be clear.

        Raises:
            ValueError: If the variable is already allocated or if there is a conflicting allocation.
            RuntimeError: If the SPAD is out of capacity.
        """
        if variable.spad_address < 0:
            assert(variable.name not in self.__var_lookup)
            # Allocate variable in SPAD
            super().allocateForce(addr, variable)
            variable.spad_address = addr
            if variable.name: # avoid dummy vars
                self.__var_lookup[variable.name] = variable
        elif addr >= 0 and variable.spad_address != addr:
            # Multiple allocations not allowed
            raise ValueError(('`variable` already allocated in address "{}", '
                              'but new allocation requested in address "{}".'.format(variable.spad_address,
                                                                                     addr)))

    def deallocate(self, addr) -> object:
        """
        Frees up the slot at the specified memory address in the memory buffer.

        Args:
            addr (int): Address of the memory slot to free.

        Raises:
            ValueError: If the address is invalid or already free.

        Returns:
            Variable: The Variable object that was contained in the deallocated slot.
        """
        retval = super().deallocate(addr)
        retval.spad_address = -1 # deallocate variable
        if retval.name: # avoid dummy vars
            self.__var_lookup.pop(retval.name)
        return retval

    def findAvailableAddress(self,
                             live_var_names,
                             replacement_policy: str = None) -> int:
        """
        Retrieves the next available SPAD address or propose an address to use if all are occupied.

        Args:
            live_var_names (set or list): A collection of variable names that are not available for replacement.
            replacement_policy (str, optional): The policy to use for determining which variables to replace.

        Returns:
            int: The first empty address, or the address to replace if all are occupied. Returns -1 if no suitable address is found.
        """
        return utilities.findAvailableLocation(self.buffer,
                                               live_var_names,
                                               replacement_policy)

    def dump(self, ostream):
        """
        Dumps the current state of the SPAD to the specified output stream.

        Args:
            ostream: The output stream to write the SPAD state to.
        """
        print('SPAD', file = ostream)
        print(f'Max Capacity, {self.CAPACITY}, Bytes', file = ostream)
        print(f'Max Capacity, {self.CAPACITY_WORDS}, Words', file = ostream)
        print(f'Current Capacity, {self.currentCapacityWords}, Words', file = ostream)
        print(f'Current Occupied, {self.CAPACITY_WORDS - self.currentCapacityWords}, Words', file = ostream)
        print("", file = ostream)
        print("address, variable, variable spad, dirty, last mload, last mstore, last cload, last cstore", file = ostream)
        last_addr = 0
        for addr, variable in enumerate(self.buffer):
            if variable is not None:
                for idx in range(last_addr, addr):
                    # empty addresses
                    print(f'{idx}, None', file = ostream)
                if variable.name:
                    spad_access_tracker = self.getAccessTracking(addr)
                    print('{}, {}, {}, {}, {}, {}, {}'.format(addr,
                                                              variable.name,
                                                              variable.spad_address,
                                                              variable.spad_dirty,
                                                              repr(spad_access_tracker.last_mload),
                                                              repr(spad_access_tracker.last_mstore),
                                                              repr(spad_access_tracker.last_cload),
                                                              repr(spad_access_tracker.last_cstore)),

                          file = ostream)
                else:
                    print('f{addr}, Dummy_{variable.tag}',
                          file = ostream)

                last_addr = addr + 1
