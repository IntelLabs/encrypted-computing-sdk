import numbers
from typing import NamedTuple

class PrioritizedPlaceholder:
    """
    Base class for priority queue items.

    This class provides a framework for items that can be used in a priority queue,
    where each item has a priority that can be dynamically adjusted. Derived classes
    can override the `_get_priority()` method to provide their own logic for determining
    priority, allowing for priorities that change on the fly.

    Priorities are expected to be tuples, and the class supports comparison operations
    based on these priorities.

    Properties:
        priority (tuple): The current priority of the item, calculated as the sum of
            the base priority and the priority delta.
        priority_delta (tuple): The current priority delta.

    Methods:
        _get_priority(): Returns the base priority of the item.
        _get_priority_delta(): Returns the priority delta of the item.
    """
    def __init__(self,
                 priority = (0, 0),
                 priority_delta = (0, 0)):
        """
        Initializes a new PrioritizedPlaceholder object.

        Args:
            priority (tuple, optional): The base priority of the item. Defaults to (0, 0).
            priority_delta (tuple, optional): The delta to be applied to the base priority. Defaults to (0, 0).
        """
        self._priority = priority
        self._priority_delta = priority_delta

    @property
    def priority(self):
        """
        Calculates and returns the current priority of the item.

        The current priority is the sum of the base priority and the priority delta.

        Returns:
            tuple: The current priority.
        """
        return tuple([sum(x) for x in zip(self._get_priority(), self.priority_delta)])

    @property
    def priority_delta(self):
        """
        Returns the current priority delta.

        Returns:
            tuple: The current delta.
        """
        return self._get_priority_delta()

    def _get_priority(self):
        """
        Returns the base priority of the item.

        Returns:
            tuple: The base priority.
        """
        return self._priority

    def _get_priority_delta(self):
        """
        Returns the priority delta of the item.

        This method can be overridden by derived classes to provide custom priority delta logic.

        Returns:
            tuple: The priority delta.
        """
        return self._priority_delta

    def __lt__(self, other):
        """
        Compares this item with another item for less-than ordering based on priority.

        Args:
            other (PrioritizedPlaceholder): The other item to compare against.

        Returns:
            bool: True if this item's priority is less than the other item's priority, False otherwise.
        """
        return self.priority < other.priority

    def __eq__(self, other):
        """
        Compares this item with another item for equality based on priority.

        Args:
            other (PrioritizedPlaceholder): The other item to compare against.

        Returns:
            bool: True if this item's priority is equal to the other item's priority, False otherwise.
        """
        return self.priority == other.priority

    def __gt__(self, other):
        """
        Compares this item with another item for greater-than ordering based on priority.

        Args:
            other (PrioritizedPlaceholder): The other item to compare against.

        Returns:
            bool: True if this item's priority is greater than the other item's priority, False otherwise.
        """
        return self.priority > other.priority

class CycleType(NamedTuple):
    """
    Named tuple to add structure to a cycle type.

    CycleType is a structured representation of a cycle, consisting of a bundle
    identifier and a cycle count within that bundle. It supports arithmetic operations
    for adding and subtracting cycles or tuples.

    Attributes:
        bundle (int): Bundle identifier or index.
        cycle (int): Clock cycle inside the specified bundle.

    Operators:
        __add__(self, other: Union[tuple, int]) -> CycleType:
            Adds a tuple or an integer to the CycleType and returns the resulting CycleType.
            If other is a tuple, only the first two elements are used for addition.
            If other is an integer, it is added to the cycle component.

        __sub__(self, other: Union[tuple, int]) -> CycleType:
            Subtracts a tuple or an integer from the CycleType and returns the resulting CycleType.
            If other is a tuple, only the first two elements are used for subtraction.
            If other is an integer, it is subtracted from the cycle component.
    """

    bundle: int
    cycle: int

    def __add__(self, other):
        """
        Adds a tuple or an integer to the `CycleType`.

        Args:
            other (Union[tuple, int]): The value to add. Can be a tuple or an integer.

        Returns:
            CycleType: The resulting `CycleType` after addition.

        Raises:
            TypeError: If `other` is not a tuple or an integer.
        """
        if isinstance(other, int):
            return self.__binaryop_cycles(other, lambda m, n: m + n)
        elif isinstance(other, tuple):
            return self.__binaryop_tuple(other, lambda m, n: m + n)
        else:
            raise TypeError('`other`: expected type `int` or `tuple`.')

    def __sub__(self, other): 
        """
        Subtracts a tuple or an integer from the `CycleType`.

        Args:
            other (Union[tuple, int]): The value to subtract. Can be a tuple or an integer.

        Returns:
            CycleType: The resulting `CycleType` after subtraction.

        Raises:
            TypeError: If `other` is not a tuple or an integer.
        """
        if isinstance(other, int):
            return self.__binaryop_cycles(other, lambda m, n: m - n)
        elif isinstance(other, tuple):
            return self.__binaryop_tuple(other, lambda m, n: m - n)
        else:
            raise TypeError('`other`: expected type `int` or `tuple`.')

    def __binaryop_cycles(self, cycles, binaryop_callable):
        """
        Performs a binary operation on the cycle component with an integer.

        Args:
            cycles (int): The integer to operate with.
            binaryop_callable (callable): The binary operation to perform.

        Returns:
            CycleType: The resulting `CycleType` after the operation.
        """
        assert(isinstance(cycles, int))
        return CycleType(self.bundle, binaryop_callable(self.cycle, cycles))

    def __binaryop_tuple(self, other, binaryop_callable):
        """
        Performs a binary operation on the `CycleType` with a tuple.

        Args:
            other (tuple): The tuple to operate with.
            binaryop_callable (callable): The binary operation to perform.

        Returns:
            CycleType: The resulting `CycleType` after the operation.
        """
        return CycleType(binaryop_callable(self.bundle, int(other[0]) if len(other) > 0 else 0),
                         binaryop_callable(self.cycle, int(other[1]) if len(other) > 1 else 0))

class CycleTracker:
    """
    Base class for tracking the clock cycle when an object is ready to be used.

    The cycle ready value is interpreted as a tuple (bundle: int, cycle: int). If the bundle
    is not used, it can always be set to `0`.

    Attributes:
        tag (Any): User-defined tag to hold any kind of extra information related to the object.

    Properties:
        cycle_ready (CycleType): Clock cycle where this object is ready to use. Uses
        :func:`~cycle_tracking.CycleTracker._get_cycle_ready` and
        :func:`~cycle_tracking.CycleTracker._set_cycle_ready`.

    Methods:
        _get_cycle_ready(): Returns the current value for the ready cycle. Derived classes can override this method
        to add their own logic to compute this value.

        _set_cycle_ready(value): Sets the current value for the ready cycle (only if the specified value is greater than
        the current `CycleTracker.cycle_ready`). Derived classes can override this method to add their own logic to compute this value.
    """

    def __init__(self, cycle_ready: CycleType):
        """
        Initializes a new CycleTracker object.

        Args:
            cycle_ready (CycleType): The initial cycle when the object is ready to be used. Must be a tuple with at least
            two elements (bundle, cycle).
        """
        assert(len(cycle_ready) > 1)
        self.__cycle_ready = CycleType(*cycle_ready)
        self.tag = 0 # User-defined tag

    @property
    def cycle_ready(self):
        """
        Gets the current cycle ready value.

        Returns:
            CycleType: The value.
        """
        return self._get_cycle_ready()

    @cycle_ready.setter
    def cycle_ready(self, value: CycleType):
        """
        Set a new cycle ready value.

        Args:
            value (CycleType): The new cycle ready value to set.
        """
        return self._set_cycle_ready(value)

    def _get_cycle_ready(self) -> CycleType:
        """
        Return the current value for the ready cycle.

        This method is called by the `cycle_ready` property getter to retrieve the value.
        Derived classes can override this method to add their own logic to compute this value.

        Returns:
            CycleType: The current value for the ready cycle.
        """
        return self.__cycle_ready

    def _set_cycle_ready(self, value: CycleType):
        """
        Set the current value for the ready cycle, only if the specified value is greater than
        the current `CycleTracker.cycle_ready`.

        This method is called by the `cycle_ready` property setter to set the new value.
        Derived classes can override this method to add their own logic to compute this value.

        Args:
            value (CycleType or tuple): New clock cycle when this object will be ready for use.
            The tuple should be in the form (bundle: int, cycle: int).
        """
        assert(len(value) > 1)
        #if self.cycle_ready < value:
        #    self.__cycle_ready = CycleType(*value)
        self.__cycle_ready = CycleType(*value)
