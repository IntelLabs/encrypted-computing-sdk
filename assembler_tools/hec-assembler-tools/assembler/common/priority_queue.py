import heapq
import bisect
import itertools

class PriorityQueue:
    """
    A priority queue implementation that supports task prioritization and ordering.

    This class allows tasks to be added with a specified priority, and supports
    operations to update, remove, and retrieve tasks based on their priority.
    """

    class __PriorityQueueIter:
        """
        An iterator for the PriorityQueue class.

        This iterator allows for iterating over the tasks in the priority queue
        while ensuring that the queue's size does not change during iteration.
        """
        def __init__(self, pq, removed):
            """
            Initializes the iterator with the priority queue and removed marker.

            Args:
                pq: The priority queue to iterate over.
                removed: The marker for removed tasks.
            """
            self.__pq = pq if pq else []
            self.__initial_len = len(self.__pq)
            self.__removed = removed
            self.__current = 0

        def __next__(self):
            """
            Returns the next task in the priority queue.

            Returns:
                tuple: The (priority, task) pair of the next task.

            Raises:
                RuntimeError: If the priority queue changes size during iteration.
                StopIteration: If there are no more tasks to iterate over.
            """
            if len(self.__pq) != self.__initial_len:
                raise RuntimeError("PriorityQueue changed size during iteration.")

            # Skip all removed tasks
            while self.__current < len(self.__pq) \
                and self.__pq[self.__current][-1] is self.__removed:
                self.__current += 1
            if self.__current >= len(self.__pq):
                raise StopIteration
            priority, _, task = self.__pq[self.__current]
            self.__current += 1 # point to nex element
            return (priority, task)


    class __PriorityTracker:
        """
        A helper class to track tasks by their priority.

        This class maintains a mapping of priorities to tasks and supports
        operations to add, find, and remove tasks based on their priority.
        """
        def __init__(self):
            """
            Initializes the priority tracker with empty mappings.
            """
            self.__priority_dict = {} # dict(int, SortedList(task)): maps priority to unordered set of tasks with same priority
            self.__priority_dict_set = {} # dict(int, set(task)): maps priority to unordered set of tasks with same priority

        def find(self, priority: int) -> object:
            """
            Finds a task with the specified priority.

            Args:
                priority (int): The priority to search for.

            Returns:
                object: A task with the specified priority, or None if not found.
            """
            return next(iter(self.__priority_dict[priority]))[1] if priority in self.__priority_dict else None

        def push(self, priority: int, tie_breaker: tuple, task: object):
            """
            Adds a task with the specified priority and tie breaker.

            Args:
                priority (int): The priority of the task.
                tie_breaker (tuple): A tuple used to break ties between tasks with the same priority.
                task (object): The task to add.

            Raises:
                ValueError: If the task is None.
            """
            if task is None:
                raise ValueError('`task` cannot be `None`.')

            if priority not in self.__priority_dict:
                self.__priority_dict[priority] = []
                assert priority not in self.__priority_dict_set
                self.__priority_dict_set[priority] = set()
            if task not in self.__priority_dict_set[priority]:
                bisect.insort_right(self.__priority_dict[priority], (tie_breaker, task))
                self.__priority_dict_set[priority].add(task)

        def pop(self, priority: int, task = None) -> object:
            """
            Removes a task with the specified priority.

            Args:
                priority (int): The priority of the task to remove.
                task (object, optional): The specific task to remove. If None, the first task is removed.

            Raises:
                KeyError: If the priority is not found.
                ValueError: If the specified task is not found in the priority.

            Returns:
                object: The task that was removed.
            """
            if priority not in self.__priority_dict:
                raise KeyError(str(priority))

            retval = None
            assert priority in self.__priority_dict_set
            if task:
                # Find index for task
                idx = next((i for i, (_, contained_task) in enumerate(self.__priority_dict[priority]) if contained_task == task),
                            len(self.__priority_dict[priority]))
                if idx >= len(self.__priority_dict[priority]):
                    raise ValueError('`task` not found in priority.')
                _, retval = self.__priority_dict[priority].pop(idx)
                assert(retval == task)
            else:
                # Remove first task
                _, retval = self.__priority_dict[priority].pop(0)
            self.__priority_dict_set[priority].remove(retval)

            if len(self.__priority_dict[priority]) <= 0:
                # Remove priority from dictionary if empty (we do not want to keep too many of these around)
                self.__priority_dict.pop(priority)
                assert len(self.__priority_dict_set[priority]) <= 0
                self.__priority_dict_set.pop(priority)
            return retval

    __REMOVED = object() # Placeholder for a removed task

    def __init__(self, queue: list = None):
        """
        Creates a new PriorityQueue object.

        Args:
            queue (list, optional): A list of (priority, task) tuples to initialize the queue.
                This is an O(len(queue)) operation.

        Raises:
            ValueError: If any task in the queue is None.
        """
        # entry: [priority: int, nonce: int, task: hashable_object]
        self.__pq = []                            # list(entry) - List of entries arranged in a heap
        self.__entry_finder = {}                  # dictionary(task: Hashable_object, entry) - mapping of tasks to entries
        self.__priority_tracker = PriorityQueue.__PriorityTracker() # Tracks tasks by priority
        self.__counter: int = itertools.count(1)   # Unique sequence count

        if queue:
            for priority, task in queue:
                if task is None:
                    raise ValueError('`queue`: tasks cannot be `None`.')
                count = next(self.__counter)
                entry = [priority, ((0, ), count), task]
                self.__entry_finder[task] = entry
                self.__priority_tracker.push(*entry)#priority, task)
                self.__pq.append()
            heapq.heapify(self.__pq)

    def __bool__(self):
        """ 
        Returns True if the priority queue is not empty, False otherwise.

        Returns:
            bool: True if it is not empty, False otherwise.
        """
        return len(self) > 0

    def __contains__(self, task: object):
        """
        Checks if a task is in the priority queue.

        Args:
            task (object): The task to check for.

        Returns:
            bool: True if it is in the queue, False otherwise.
        """
        return task in self.__entry_finder

    def __iter__(self):
        """
        Returns an iterator over the tasks in the priority queue.

        Returns:
            __PriorityQueueIter: An iterator over the tasks in the queue.
        """
        return PriorityQueue.__PriorityQueueIter(self.__pq, PriorityQueue.__REMOVED)

    def __len__(self):
        """
        Returns the number of tasks in the priority queue.

        Returns:
            int: The number of tasks.
        """
        return len(self.__entry_finder)

    def __repr__(self):
        """
        Returns a string representation of the priority queue.

        Returns:
            str: A string representation of the queue.
        """
        return '<{} object at {}>(len={}, pq={})'.format(type(self).__name__,
                                                         hex(id(self)),
                                                         len(self),
                                                         self.__pq)

    def push(self, priority: int, task: object, tie_breaker: tuple = None): #ahead: bool = None):
        """
        Adds a new task or update the priority of an existing task.

        Args:
            priority (int): The priority of the task.
            task (object): The task to add or update.
            tie_breaker (tuple, optional): A tuple of ints to use as a tie breaker for tasks
                of the same priority. Defaults to (0,) if None.

        Raises:
            ValueError: If the task is None.
            TypeError: If the tie_breaker is not a tuple of ints or None.
        """
        if task is None:
            raise ValueError('`task` cannot be `None`.')
        if tie_breaker is not None \
           and not all(isinstance(x, int) for x in tie_breaker):
            raise TypeError('`tie_breaker` expected tuple of `int`s, or `None`.')
        b_add_needed = True
        if task in self.__entry_finder:
            old_priority, (old_tie_breaker, _), _ = self.__entry_finder[task]
            if tie_breaker is None:
                tie_breaker = old_tie_breaker
            if old_priority != priority \
               or tie_breaker != old_tie_breaker:
                self.remove(task)
            else:
                # same task without priority change detected: no need to add
                b_add_needed = False

        if tie_breaker is None:
            tie_breaker = (0,)

        if b_add_needed:
            if len(self.__pq) == 0:
                self.__counter: int = itertools.count(1) # restart sequence count when queue is empty
            count = next(self.__counter)
            entry = [priority, (tie_breaker, count), task]
            self.__entry_finder[task] = entry
            self.__priority_tracker.push(*entry)#priority, task)
            heapq.heappush(self.__pq, entry)

    def remove(self, task: object):
        """
        Removes an existing task from the priority queue.

        Args:
            task (object): The task to remove from the queue. It must exist.

        Raises:
            KeyError: If the task is not found in the queue.
        """
        # mark an existing task as PriorityQueue.__REMOVED.
        entry = self.__entry_finder.pop(task)
        priority, *_ = entry
        self.__priority_tracker.pop(priority, task) # remove it from the priority tracker
        entry[-1] = PriorityQueue.__REMOVED

    def peek(self) -> tuple:
        """
        Returns the task with the lowest priority without removing it from the queue.

        Returns:
            tuple: The (priority, task) pair of the task with the lowest priority,
            or None if the queue is empty.
        """
        # make sure head is not a removed task
        while self.__pq and self.__pq[0][-1] is PriorityQueue.__REMOVED:
            heapq.heappop(self.__pq)
        retval = None
        if self.__pq:
            priority, _, task = self.__pq[0]
            retval = (priority, task)
        return retval

    def find(self, priority: int) -> object:
        """
        Returns a task with the specified priority, if there is one.

        The returned task is not removed from the priority queue.

        Args:
            priority (int): The priority of the task to find.

        Returns:
            object: The task with the specified priority, or None if no such task exists.
        """
        return self.__priority_tracker.find(priority)

    def pop(self) -> tuple:
        """
        Removes and return the task with the lowest priority.

        Returns:
            tuple: The (priority, task) pair of the task that was removed.

        Raises:
            IndexError: If the queue is empty.
        """
        task = PriorityQueue.__REMOVED
        while task is PriorityQueue.__REMOVED: # make sure head is not a removed task
            priority, _, task = heapq.heappop(self.__pq)
        self.__entry_finder.pop(task)
        self.__priority_tracker.pop(priority, task)
        return (priority, task)
