from assembler.common import constants

class MemoryBank:
    """
    Base class for memory banks.

    This class simulates a memory bank and its locations, where each address in the memory bank's buffer
    represents a slot with space for a word.

    Constructors:
        MemoryBank(data_capacity_words: int)
            Creates a MemoryBank with a specified capacity in words.

        fromCapacityBytes(data_capacity_bytes: int) -> MemoryBank
            Creates a MemoryBank with a specified capacity in bytes.

    Attributes:
        _current_data_capacity_words (int): Protected attribute representing the current capacity in words.
            This is typically modified when allocating or deallocating spaces in the memory bank buffer.

    Properties:
        CAPACITY (int): Total capacity of the memory bank in bytes.
        CAPACITY_WORDS (int): Total capacity of the memory bank in words.
        buffer (list): The memory bank's buffer, allocated to hold up to CAPACITY_WORDS objects.
            If `buffer[i]` is None, then index `i` (address) is considered an empty/available memory slot.
        currentCapacityWords (int): Current available capacity for the memory bank in words.

    Methods:
        allocateForce(addr: int, obj: object)
            Forces allocation of an existing object at a specific address.

        deallocate(addr: int) -> object
            Frees up the slot at the specified memory address in the memory buffer.
    """

    # Constructor wrappers
    # --------------------

    @classmethod
    def fromCapacityBytes(cls, data_capacity_bytes: int):
        """
        Creates a new MemoryBank object with a specified capacity in bytes.

        Args:
            data_capacity_bytes (int): Maximum capacity in bytes for the memory bank.

        Returns:
            MemoryBank: A new instance of MemoryBank with the specified capacity.
        """
        return cls(constants.convertBytes2Words(data_capacity_bytes))

    # Constructor
    # -----------

    def __init__(self,
                 data_capacity_words: int):
        """
        Initializes a new MemoryBank object with a specified capacity in words.

        Args:
            data_capacity_words (int): Maximum capacity in words for the memory bank.

        Raises:
            ValueError: If the capacity is not a positive number.
        """
        if data_capacity_words <= 0:
            raise ValueError(("`data_capacity_words` must be a positive number, "
                              "but {} received.".format(data_capacity_words)))
        self.__data_capacity_words = data_capacity_words # max capacity in words
        self.__data_capacity = constants.convertWords2Bytes(data_capacity_words)
        self.__buffer = [None for _ in range(self.__data_capacity_words)]
        self._current_data_capacity_words = self.__data_capacity_words

    # Methods and properties
    # ----------------------

    @property
    def CAPACITY(self):
        """
        Gets the total capacity of the memory bank in bytes.

        Returns:
            int: The total capacity in bytes.
        """
        return self.__data_capacity

    @property
    def CAPACITY_WORDS(self):
        """
        Gets the total capacity of the memory bank in words.

        Returns:
            int: The total capacity in words.
        """
        return self.__data_capacity_words

    @property
    def currentCapacityWords(self):
        """
        Gets the current available capacity for the memory bank in words.

        Returns:
            int: The current available capacity in words.
        """
        return self._current_data_capacity_words

    @property
    def buffer(self):
        """
        Gets the memory bank's buffer.

        Returns:
            list: The buffer allocated to hold up to CAPACITY_WORDS objects.
        """
        return self.__buffer

    def allocateForce(self,
                      addr: int,
                      obj: object):
        """
        Force the allocation of an existing object at a specific address.

        Each object is considered to occupy one word. The current capacity is decreased by one word.
        This method returns immediately if the object is already allocated to the specified address.

        Args:
            addr (int): Address in the memory bank where to allocate the object. Must not be already occupied by a different object.
            obj (object): Object to allocate. It will be assigned to `buffer[addr]`.

        Raises:
            ValueError: If the address is out of range or already occupied by a different object.
            RuntimeError: If the memory bank is out of capacity.
        """
        if self.currentCapacityWords <= 0:
            raise RuntimeError("Critical error: Out of memory.")
        if addr < 0 or addr >= len(self.buffer):
            raise ValueError(("`addr` out of range. Must be in range [0, {}),"
                              "but {} received.".format(len(self.buffer), addr)))
        if not self.buffer[addr]:
            # track the obj our buffer
            self.buffer[addr] = obj
            # update capacity
            self._current_data_capacity_words -= 1
        else:
            if self.buffer[addr] != obj:
                raise ValueError("`addr` {} already occupied.".format(addr))

    def deallocate(self, addr) -> object:
        """
        Free up the slot at the specified memory address in the memory buffer.

        Args:
            addr (int): Address of the memory slot to free.

        Raises:
            ValueError: If the address is out of range or already free.

        Returns:
            object: The object that was contained in the deallocated slot.
        """
        if addr < 0 or addr >= len(self.buffer):
            raise ValueError(("`addr` out of range. Must be in range [0, {}),"
                              "but {} received.".format(len(self.buffer), addr)))

        obj = self.buffer[addr]
        if not obj:
            raise ValueError('`addr`: Adress "{}" is already free.'.format(addr))

        self.buffer[addr] = None
        self._current_data_capacity_words += 1

        return obj
