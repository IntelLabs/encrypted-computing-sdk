
from assembler.common.constants import Constants
from assembler.common.cycle_tracking import CycleType
from assembler.common.priority_queue import PriorityQueue

def computePriority(variable, replacement_policy):
    """
    Computes the priority for reusing the location of a specified variable.

    The priority is determined based on the replacement policy. The smaller the priority value,
    the higher the priority for reuse. Tuples are used for staged comparisons.

    Args:
        variable (Variable): The variable for which to compute the priority.
        replacement_policy (str): The policy to use for determining priority. Must be one of
            `Constants.REPLACEMENT_POLICIES`.

    Returns:
        tuple: A tuple representing the priority for reusing the variable's location.
    """
    retval = (float("-inf"), ) # Default: highest priority if no variable
    if variable:
        # Register in use
        # last_x_access = variable.last_x_access.bundle * Constants.MAX_BUNDLE_SIZE + variable.last_x_access.cycle \
        last_x_access = variable.last_x_access if variable.last_x_access \
                        else CycleType(0, 0)
        if replacement_policy == Constants.REPLACEMENT_POLICY_FTBU:
            if variable.accessed_by_xinsts:
                # Priority by
                retval = (-variable.accessed_by_xinsts[0].index, # Largest (furthest) accessing instruction
                          *last_x_access, # Oldest accessed cycle (oldest == smallest)
                          len(variable.accessed_by_xinsts)) # How many more uses this variable has
        elif replacement_policy == Constants.REPLACEMENT_POLICY_LRU:
            # Priority by oldest accessed cycle (oldest == smallest)
            retval = (*last_x_access, )
        else:
            raise ValueError(f'`replacement_policy`: invalid value "{replacement_policy}". Expected value in {REPLACEMENT_POLICIES}.')
    return retval

def flushRegisterBank(register_bank,
                      current_cycle: CycleType,
                      replacement_policy,
                      live_var_names = None,
                      pct: float = 0.5):
    """
    Cleans up a register bank by removing variables assigned to registers.

    The function attempts to free up to pct * 100% of registers. Only non-dirty registers
    that do not contain live variables are cleaned up. Dummy variables are considered live.

    Args:
        register_bank (RegisterBank):
            The register bank to clean up.
        current_cycle (CycleType):
            The current cycle to consider for readiness.
        replacement_policy (str):
            The policy to use for determining which variables to replace.
            Must be one of `Constants.REPLACEMENT_POLICIES`.
        live_var_names (set or list, optional):
            A collection of variable names that are not available
            for replacement. Defaults to None.
        pct (float, optional):
            The fraction of the register bank to clean up. Defaults to 0.5.
    """
    local_heap = PriorityQueue()
    occupied_count: int = 0
    for idx, reg in enumerate(register_bank):
        # Traverse the registers in the bank and put occupied, non-dirty ones
        # in a heap where priority is based on replacement_policy
        v = reg.contained_variable
        if v is not None:
            occupied_count += 1
            if not reg.register_dirty \
               and (v.name and v.name not in live_var_names) \
               and current_cycle >= v.cycle_ready:
                # Variable can be cleared from the register if needed
                priority = computePriority(v, replacement_policy)
                local_heap.push(priority, reg, (idx, ))

    # Clean up registers until we reach the specified pct occupancy or we have
    # no registers left that can be cleaned up
    while local_heap \
          and occupied_count / register_bank.register_count > pct:
        _, reg = local_heap.pop()
        reg.allocateVariable(None)
        occupied_count -= 1

def findAvailableLocation(vars_lst,
                          live_var_names,
                          replacement_policy: str = None):
    """
    Retrieves the index of the next available location in a collection of Variable objects.

    The function proposes a location to use if all are occupied, based on a replacement policy.
    Locations with dummy variables (with empty names) are considered live and will not be selected.

    Args:
        vars_lst (iterable):
            An iterable collection of Variable objects. Can contain `None`s.
        live_var_names (set or list):
            A collection of variable names that are not available for replacement.
        replacement_policy (str, optional):
            The policy to use for determining which variables to replace.
            Must be one of `Constants.REPLACEMENT_POLICIES`. Defaults to None.

    Raises:
        ValueError: If the replacement policy is invalid.

    Returns:
        int: The index of the first empty location found in `vars_lst`, or the index of the suggested
        location to replace if `vars_lst` is full and a replacement policy was specified. Returns -1
        if no suitable location is found.
    """
    if replacement_policy and replacement_policy not in Constants.REPLACEMENT_POLICIES:
        raise ValueError(('`replacement_policy`: invalid value "{}". '
                            'Expected value in {} or None.').format(replacement_policy,
                                                                    Constants.REPLACEMENT_POLICIES))

    retval = -1
    priority = (float("inf"), float("inf"), float("inf"))
    for idx, v in enumerate(vars_lst):
        if not v:
            retval = idx
            break # Found an empty spot
        elif replacement_policy \
            and (v.name and v.name not in live_var_names): # Avoids dummy variables
            # Find priority for replacement of this location
            v_priority = computePriority(v, replacement_policy)
            if v_priority < priority:
                retval = idx
                priority = v_priority
    # At this point, highest priority location has been found in `retval`, if any

    return retval
