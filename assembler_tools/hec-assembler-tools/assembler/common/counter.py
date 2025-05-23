
import itertools

class Counter:
    """
    Provides counters that can be globally reset.

    This class allows for the creation of counters that can be iterated over and reset
    to their initial start values. It supports creating multiple counters with different
    start and step values, and provides functionality to reset individual counters or all
    counters at once.
    """

    class CounterIter:
        """
        An iterator for generating evenly spaced values.

        This iterator starts at a specified value and increments by a specified step.
        It can be reset to start over from its initial start value.
        """
        def __init__(self, start = 0, step = 1):
            """
            Initializes a new CounterIter object.

            Args:
                start (int, optional): The starting value of the counter. Defaults to 0.
                step (int, optional): The step value for the counter. Defaults to 1.
            """
            self.__start = start
            self.__step = step
            self.__counter = None # itertools.counter
            self.reset()

        def __next__(self):
            """
            Returns the next value in the counter sequence.

            Returns:
                int: The next value.
            """
            return next(self.__counter)

        @property
        def start(self) -> int:
            """
            Gets the start value for this counter.

            Returns:
                int: The start value.
            """
            return self.__start

        @property
        def step(self) -> int:
            """
            Gets the step value for this counter.

            Returns:
                int: The step value.
            """
            return self.__step

        def reset(self):
            """
            Resets this counter to start from its `start` value.
            """
            self.__counter = itertools.count(self.start, self.step)

    __counters = set()

    @classmethod
    def count(cls, start = 0, step = 1) -> CounterIter:
        """
        Creates a new counter iterator that returns evenly spaced values.

        Args:
            start (int, optional): The starting value of the counter. Defaults to 0.
            step (int, optional): The step value for the counter. Defaults to 1.

        Returns:
            CounterIter: An iterator that generates evenly spaced values starting from `start`.
        """
        retval = cls.CounterIter(start, step)
        cls.__counters.add(retval)
        return retval

    @classmethod
    def reset(cls, counter: CounterIter = None):
        """
        Reset the specified counter, or all counters if none is specified.

        This method resets the specified counter, or all counters, to start
        over from their respective `start` values.

        Args:
            counter (CounterIter, optional): The counter to reset.
            If None, all counters are reset.
        """
        counters_to_reset = cls.__counters if counter is None else { counter }
        for c in counters_to_reset:
            c.reset()
