from collections import deque

class QueueDict:
    """
    A dictionary that keeps its elements in a FIFO (queue) order.

    This class allows adding new items to the dictionary, but they will always be
    added at the end of the queue structure. Modifying the value of an existing
    key will not change the order of the item in the queue structure.

    Read/write access to contained items via their keys is allowed, but removal
    of items occur at the start of the queue structure only. No removals
    are allowed on any other items of the structure.
    """
    def __init__(self):
        """
        Initializes a new, empty QueueDict object.
        """
        self.__q = deque()
        self.__lookup = {}

    def __len__(self) -> int:
        """
        Returns the number of items in the QueueDict.

        Returns:
            int: Number of items.
        """
        return len(self.__lookup)

    def __iter__(self):
        """
        Returns an iterator over the keys of the QueueDict.

        Yields:
            The next key in the QueueDict.

        Raises:
            RuntimeError: If the QueueDict changes size during iteration.
        """
        q = self.__q.copy()
        initial_len = len(self.__lookup)
        while q:
            if len(self.__lookup) != initial_len:
                raise RuntimeError("QueueDict changed size during iteration.")
            key = q.popleft()
            yield key

    def __contains__(self, key) -> bool:
        """
        Checks if a key is in the QueueDict.

        Args:
            key: The key to check for.

        Returns:
            bool: True if the key is in the QueueDict, False otherwise.
        """
        return key in self.__lookup

    def __getitem__(self, key) -> object:
        """
        Gets the value associated with a key in the QueueDict.

        Args:
            key: The key whose value is to be retrieved.

        Returns:
            object: The value associated with the key.
        """
        return self.__lookup[key]

    def __setitem__(self, key, value: object):
        """
        Sets the value associated with a key in the QueueDict.

        Args:
            key: The key to set the value for.
            value: The value to associate with the key.
        """
        self.push(key, value)

    def clear(self):
        """
        Empties the QueueDict, removing all items.
        """
        self.__q.clear()
        self.__lookup = {}

    def copy(self) -> object: # QueueDict
        """
        Returns a shallow copy of the QueueDict.

        Returns:
            QueueDict: The shallow copy.
        """
        retval = QueueDict()
        retval.__q = self.__q.copy()
        retval.__lookup = self.__lookup.copy()
        return retval

    def peek(self) -> tuple:
        """
        Returns the (key, value) pair item at the start of the QueueDict, but does
        not modify the QueueDict.

        This is the next item that would be removed on the next call to `QueueDict.pop()`.

        Returns:
            tuple: The (key, value) pair.
        """
        key = self.__q[0]
        value = self.__lookup[key]
        return (key, value)

    def pop(self) -> tuple:
        """
        Removes and returns the (key, value) pair item at the start of the QueueDict.
        
        Returns:
            tuple: The (key, value) pair that was removed.
        """
        key = self.__q.popleft()
        value = self.__lookup.pop(key)
        return (key, value)

    def push(self, key, value: object):
        """
        Adds a new (key, value) pair item at the end of the QueueDict if `key` does not
        exists in the QueueDict. Otherwise, the value of the existing item with specified
        key is changed to the new `value`.

        This method is equivalent to assigning a value to the key: `QueueDict[key] = value`.

        Args:
            key: The key to add or update.
            value: The value to associate with the key.
        """
        if key not in self.__lookup:
            self.__q.append(key)
        self.__lookup[key] = value
