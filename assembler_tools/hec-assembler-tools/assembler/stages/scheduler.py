import collections
import heapq
import networkx as nx
from typing import NamedTuple

from . import buildVarAccessListFromTopoSort
from assembler.common.cycle_tracking import PrioritizedPlaceholder, CycleType
from assembler.instructions import xinst, cinst, minst
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable
from pickle import TRUE

def __orderKeygenVars(mem_model: MemoryModel) -> list:
    """
    Returns the name of the keygen variables in the order they have to be generated.

    Parameters:
        mem_model (MemoryModel): Completed memory model corresponding to the specified dependency graph and
                                 input mem info. Used to extract the keygen variable information.

    Raises:
        RuntimeError: Detected missing keygen variable in ordering.

    Returns:
        list: A list of lists. Each element of the outer list represents a seed. Each element
              in the inner list is the name of the keygen variable corresponding to that index
              ordering for the corresponding seed.
    """
    retval = list([] for _ in range(len(mem_model.meta_keygen_seed_vars)))
    for var_name, (seed_idx, key_idx) in mem_model.keygen_variables.items():
        assert seed_idx < len(retval)
        if key_idx >= len(retval[seed_idx]):
            retval[seed_idx] += ((key_idx - len(retval[seed_idx]) + 1) * [None])
        retval[seed_idx][key_idx] = var_name
    # Validate that no key material was skipped
    for seed_idx, l in enumerate(retval):
        for key_idx, var_name in enumerate(l):
            if var_name is None:
                raise RuntimeError(f'Detected key material {key_idx} generation skipped for seed {seed_idx}.')

    return retval

def __findVarInPrevDeps(deps_graph: nx.DiGraph,
                        instr_id: tuple,
                        var_name: str,
                        b_only_sources: bool = False) -> tuple:
    """
    Returns the ID for an instruction that uses the specified variable, and is
    a dependency for input instruction.

    Parameters:
        deps_graph (nx.DiGraph): Completed graph of dependencies among the instructions in the input listing.
        instr_id (tuple): ID of instruction for which to find dependency.
        var_name (str): Name of the variable that must be present in dependency.
        b_only_sources (bool, optional): If True, only source variables are scanned. Otherwise, all variables are
                                         checked when determining if `var_name` is in dependency instruction.

    Returns:
        tuple or None: ID of first instruction found which is direct or indirect
                       dependency of `instr_id` in the dependency graph. The returned instruction
                       must have `var_name` as one of its variables. If no instruction is found,
                       returns None.
    """
    retval = None

    if instr_id in deps_graph:
        checked_instructions = set() # avoids checking same instruction multiple times
        dep_instructions = collections.deque()
        last_instr = deps_graph.nodes[instr_id]["instruction"]
        # Repeat while we have instructions to process and we haven't found what we need
        while last_instr is not None and retval is None:
            # Add predecessors of last instruction to stack of predecessors
            preds = (deps_graph.nodes[i_id]["instruction"] for i_id in deps_graph.predecessors(last_instr.id))
            for x in preds:
                if x.id not in checked_instructions:
                    dep_instructions.append(x)
            # Work on next instruction
            last_instr = dep_instructions.pop() if len(dep_instructions) > 0 else None
            if last_instr is not None:
                checked_instructions.add(last_instr.id)
                # Check if var_name is present in instruction
                sources = set(src_var.name for src_var in last_instr.sources if isinstance(src_var, Variable))
                dests = set(dst_var.name for dst_var in last_instr.sources if not b_only_sources and isinstance(dst_var, Variable))
                if var_name in sources | dests:
                    # var_name found: return the instruction
                    retval = last_instr.id

    return retval

def enforceKeygenOrdering(deps_graph: nx.DiGraph,
                          mem_model: MemoryModel,
                          verbose_ostream = None):
    """
    Given the dependency graph for instructions and a complete memory model, injects
    instructions and dependencies to enforce ordering required for the keygen subsystem.

    For all keygen variables of the same seed, `copy` instructions are injected and
    all instructions using the same keygen variable as the `copy` instruction become
    dependent of said `copy`. This ensures that the variable is generated before it is
    used. Furthermore, `copy` instructions depend on each other based on the ordering
    of the keygen variables. This ensures correct ordering of key material generation.

    Parameters:
        deps_graph (nx.DiGraph): Completed graph of dependencies among the instructions in the input listing.
                                 Will be changed with the injected instructions and dependencies.
        mem_model (MemoryModel): Completed memory model corresponding to the specified dependency graph and
                                 input mem info. Will be changed if new variables are needed during injection.
        verbose_ostream: Stream where to print verbose output (object with a `write` method).
                         If None, no verbose output occurs.
    """

    # this function enforces the following dependency ordering:
    #
    # copy kg_var_0  ->  op kg_var_0
    #                ->  op kg_var_0
    #                ->  op kg_var_0
    #                    ...
    #                ->  copy kg_var_1  ->  op kg_var_1
    #                                   ->  op kg_var_1
    #                                   ->  op kg_var_1
    #                                       ...
    #                                   ->  copy kg_var_2 -> ...
    #
    # This ordering ensures that kg_var_X is generated the first time its copy
    # instruction is met and all the other uses can then occur with the generated
    # value. Then, kg_var_X+1 can also be generated after kg_var_X has been generated
    # without needing to wait for all kg_var_X uses to occur (only the first copy).

    ordered_kg_vars = __orderKeygenVars(mem_model)

    if ordered_kg_vars and verbose_ostream:
        print("Enforcing keygen ordering", file = verbose_ostream)

    for seed_idx, kg_seed_list in enumerate(ordered_kg_vars):
        if verbose_ostream:
            print(f"Seed {seed_idx} / {len(ordered_kg_vars)}", file = verbose_ostream)
        last_copy_id = None
        b_copy_deps_found = False # tracks whether we have correctly added dependencies for the new copy
        for key_idx, kg_var_name in enumerate(kg_seed_list):
            # Create a copy instruction and make all instructions using this kg var depend on it
            src = mem_model.variables[kg_var_name]
            # Create temp target variable
            dst = mem_model.retrieveVarAdd(mem_model.findUniqueVarName(), src.suggested_bank)
            copy_instr = xinst.Copy(0, # id
                                    0, # N
                                    [ dst ],
                                    [ src ],
                                    comment=f'injected copy to generate keygen var {kg_var_name} (seed = {seed_idx}, key = {key_idx})')
            deps_graph.add_node(copy_instr.id, instruction=copy_instr)
            # Enforce ordering of copies based on ordering of keygen
            if last_copy_id is not None:
                # Last copy -> current copy
                deps_graph.add_edge(last_copy_id, copy_instr.id)
            last_copy_id = copy_instr.id

            for instr_id in deps_graph:
                if instr_id != copy_instr.id \
                   and kg_var_name in set(src.name for src in deps_graph.nodes[instr_id]['instruction'].sources):
                    # Found instruction that uses the kg var:

                    if not b_copy_deps_found:
                        # Find out if this instruction does not depend on another
                        # instruction that uses the same kg var
                        if __findVarInPrevDeps(deps_graph, instr_id, kg_var_name, b_only_sources=True) is None:
                            # instr_id does not depend on this kg variable:
                            # make its dependencies same as the injected copy in order to avoid
                            # copy being executed before it is needed
                            for dependency_id in deps_graph.predecessors(instr_id):
                                # dependency -> copy_instr
                                deps_graph.add_edge(dependency_id, copy_instr.id)

                            b_copy_deps_found = True # found artificial dependencies for copy

                    # Make instruction depend on this injected copy
                    # copy_instr -> instr
                    deps_graph.add_edge(copy_instr.id, instr_id)

    if ordered_kg_vars and verbose_ostream:
        print(f"Seed {len(ordered_kg_vars)} / {len(ordered_kg_vars)}", file = verbose_ostream)
    # We should not have introduced any cycles with these modifications
    assert nx.is_directed_acyclic_graph(deps_graph)

def generateInstrDependencyGraph(insts_listing: list,
                                 verbose_ostream = None) -> nx.DiGraph:
    """
    Given a pre-processed P-ISA instructions listing, generates a dependency graph
    for the instructions based on their inputs and outputs, and any shared HW resources
    among instructions.

    Parameters:
        insts_listing (list): List of pre-processed P-ISA instructions.
        verbose_ostream: Stream where to print verbose output (object with a `write` method).
                         If None, no verbose output occurs.

    Raises:
        nx.NetworkXUnfeasible: Input listing results in a dependency graph that is not a Directed Acyclic Graph.

    Returns:
        nx.DiGraph: A Directed Acyclic Graph representing the dependencies among the
                    instructions in the input listing.
    """
    # Uses dynamic programming to track dependencies

    class VarTracking(NamedTuple):
        # Used for clarity
        last_write: object # last instruction that wrote to this variable
        reads_after_last_write: list # all insts that read from this variable after last write

    retval = nx.DiGraph()

    verbose_report_every_x_insts = 1
    if verbose_ostream:
        verbose_report_every_x_insts = len(insts_listing) // 10
    if verbose_report_every_x_insts < 1:
        verbose_report_every_x_insts = 1

    # Look up table for already seen variables
    vars2insts = {} # dict(var_name, VarTracking )
    for idx, inst in enumerate(insts_listing):

        if verbose_ostream:
            if idx % verbose_report_every_x_insts == 0:
                print("{}% - {}/{}".format(idx * 100 // len(insts_listing),
                                           idx,
                                           len(insts_listing)), file = verbose_ostream)

        # Add new node
        # All instructions are nodes
        retval.add_node(inst.id, instruction=inst)

        # Find dependencies:
        # prev_inst(x, dst) -> inst(dst, src)
        # prev_inst(dst, x) -> inst(dst, src)
        # prev_inst(src, x) -> inst(dst, src)

        for variable in inst.dests:
            # Add dependencies
            if variable.name in vars2insts:
                # Check if last read
                if vars2insts[variable.name].reads_after_last_write:
                    # Add deps to all reads after last write
                    for inst_dep in vars2insts[variable.name].reads_after_last_write:
                        if inst_dep.id != inst.id:
                            retval.add_edge(inst_dep.id, inst.id)
                else: # Add dep to last write
                    inst_dep = vars2insts[variable.name].last_write # last instruction that wrote to this variable
                    if inst_dep and inst_dep.id != inst.id:
                        retval.add_edge(inst_dep.id, inst.id)
            # Record write
            vars2insts[variable.name] = VarTracking( inst, [] ) # (last inst that wrote to this, all insts that read from it after last write)

        for variable in inst.sources:
            if variable.name in vars2insts:
                # Add dependency to last write
                inst_dep = vars2insts[variable.name].last_write # last instruction that wrote to this variable
                if inst_dep and inst_dep.id != inst.id:
                    retval.add_edge(inst_dep.id, inst.id)
            else:
                # First time seeing this var
                vars2insts[variable.name] = VarTracking( None, [] )
            # Record read
            vars2insts[variable.name].reads_after_last_write.append(inst)

    # Different variants to enforce ordering

    #print('##### DEBUG #####')
    ### sequential instructions (no reordering)
    #print('***** Sequential *****')
    #for idx in range(len(insts_listing) - 1):
    #    retval.add_edge(insts_listing[idx].id, insts_listing[idx + 1].id)

    ## tw before rshuffle
    #print('***** twid before rshuffle *****')
    #for idx in range(len(insts_listing) - 1):
    #    if isinstance(insts_listing[idx], xinst.rShuffle):
    #        if isinstance(insts_listing[idx + 1], xinst.twNTT):
    #            print(insts_listing[idx].id)
    #            retval.add_edge(insts_listing[idx + 1].id, insts_listing[idx].id)

    # rshuffle before tw
    #print('***** rshuffle before twid *****')
    #for idx in range(len(insts_listing) - 1):
    #    if isinstance(insts_listing[idx], xinst.rShuffle):
    #        if isinstance(insts_listing[idx + 1], xinst.twNTT):
    #            print(insts_listing[idx].id)
    #            retval.add_edge(insts_listing[idx].id, insts_listing[idx + 1].id)

    # rshuffles ordered
    #print('***** Ordered rshuffles *****')
    #for idx in range(len(insts_listing) - 1):
    #    if isinstance(insts_listing[idx], xinst.rShuffle):
    #        for j in range(len(insts_listing) - idx):
    #            jdx = j + idx + 1
    #            if isinstance(insts_listing[jdx], xinst.rShuffle):
    #                print(insts_listing[idx].id)
    #                retval.add_edge(insts_listing[idx].id, insts_listing[jdx].id)
    #                break

    # twid ordered
    #print('***** Ordered twntt *****')
    #for idx in range(len(insts_listing) - 1):
    #    if isinstance(insts_listing[idx], xinst.twNTT):
    #        for jdx in range(idx + 1, len(insts_listing)):
    #            if isinstance(insts_listing[jdx], xinst.twNTT):
    #                print(insts_listing[idx].id)
    #                retval.add_edge(insts_listing[idx].id, insts_listing[jdx].id)
    #                break

    # Detect cycles in result
    if not nx.is_directed_acyclic_graph(retval):
        raise nx.NetworkXUnfeasible('Instruction listing must form a Directed Acyclic Graph dependency.')

    if verbose_ostream:
        print("100% - {0}/{0}".format(len(insts_listing)), file = verbose_ostream)

    # retval contains the dependency graph
    return retval

def schedulePISAInstructions(dependency_graph: nx.DiGraph,
                             progress_verbose: bool = False) -> (list, int, int):
    """
    Given the dependency directed acyclic graph of XInsts, returns a schedule
    for the corresponding P-ISA instructions, that minimizes idle cycles.

    Parameters:
        dependency_graph (nx.DiGraph): The dependency graph of XInsts.
        progress_verbose (bool, optional): If True, prints progress information. Defaults to False.

    Returns:
        tuple: A tuple containing:
            - list: The scheduled instructions.
            - int: The total number of idle cycles.
            - int: The number of NOPs inserted.
    """
    class PrioritizedInstruction(PrioritizedPlaceholder):
        def __init__(self,
                     instruction,
                     priority_delta = (0, 0)):
            super().__init__(priority_delta=priority_delta)
            self.__instruction = instruction

        def __repr__(self):
            return '<{} (priority = {})>(instruction={}, priority_delta={})'.format(type(self).__name__,
                                                                                    self.priority,
                                                                                    repr(self.instruction),
                                                                                    self.priority_delta)

        @property
        def instruction(self):
            return self.__instruction

        def _get_priority(self):
            return self.instruction.cycle_ready

    retval = []
    topo_sort = buildVarAccessListFromTopoSort(dependency_graph)
    dependency_graph = nx.DiGraph(dependency_graph) # make a copy of the incoming graph to avoid modifying input
    total_idle_cycles = 0
    num_nops = 0
    set_processed_instrs = set() # track instructions that have been process to avoid encountering them after scheduling
    current_cycle = CycleType(bundle = 0, cycle = 1)
    p_queue = [] # Sorted list by priority: ready cycle
    b_changed = True # Track when there are changes in the priority queue or dependency graph
    total_insts = dependency_graph.number_of_nodes()
    prev_report_pct = -1
    while dependency_graph:

        if progress_verbose:
            pct = int(len(retval) * 100 / total_insts)
            if pct > prev_report_pct and pct % 10 == 0:
                prev_report_pct = pct
                print(f"{pct}% - {len(retval)}/{total_insts}")
        if b_changed: # If priority queue or dependency graph have changed since last iteration

            # Extract all the instructions that can be executed without dependencies
            # and merge to current instructions that can be executed without dependencies
            last_idx = -1
            for idx, instr_id in enumerate(topo_sort):
                if instr_id not in set_processed_instrs:
                    if dependency_graph.in_degree(instr_id) > 0:
                        # Found first instruction with dependencies
                        break
                    instr = dependency_graph.nodes[instr_id]['instruction']
                    p_queue.append(PrioritizedInstruction(instr))
                    set_processed_instrs.add(instr.id)
                last_idx = idx
            # Remove all instructions that got queued for scheduling
            if last_idx >= 0:
                topo_sort = topo_sort[last_idx + 1:]

            # Reorder priority queue since the items' priorities may change after scheduling an instruction
            assert(p_queue)
            heapq.heapify(p_queue)

        # Schedule next instruction

        # See if there is an immediate instruction we can queue
        element_idx = 0
        for idx, p_inst in enumerate(p_queue):
            if p_inst.instruction.cycle_ready == current_cycle:
                element_idx = idx
                break

        # Instruction can be immediate in mid queue or
        # the head of the queue if no immediate was found.
        instr = p_queue[element_idx].instruction

        if instr.cycle_ready > current_cycle:
            # We need nops because next instruction is not ready
            num_idle_cycles = instr.cycle_ready.cycle - current_cycle.cycle
            total_idle_cycles += num_idle_cycles
            # Make new instruction to execute a nop
            instr = xinst.Nop(instr.id[0], num_idle_cycles)
            num_nops += 1
            b_changed = False # No changes in the queue or graph

            # Do not pop actual instruction from graph or queue since we had to add nops before its scheduling
        else:
            # Instruction ready: pop instruction from queue and update dependency graph
            # (this breaks the heap invariant for p_queue, but we heapify
            # on every iteration due to priorities changing based on latency)
            p_queue = p_queue[:element_idx] + p_queue[element_idx + 1:]
            dependents = list(dependency_graph.neighbors(instr.id)) # find instructions that depend on this instruction
            dependency_graph.remove_node(instr.id) # remove from graph to update the in_degree of dependendent instrs
            # "move" dependent instrs that have no other dependencies to the top of the topo sort
            topo_sort = [ instr_id for instr_id in dependents if dependency_graph.in_degree(instr_id) <= 0 ] + topo_sort
            # Do not search the topo sort to actually remove the duplicated instrs because it is O(N) costly:
            # set_processed_instrs will take care of skipping them once encountered.
            b_changed = True # queue and/or graph changed

        cycle_throughput = instr.schedule(current_cycle, len(retval) + 1) # simulate execution to update cycle ready of dependents
        retval.append(instr)

        # Next cycle starts
        current_cycle += cycle_throughput

    if progress_verbose:
        print(f"100% - {total_insts}/{total_insts}")

    return retval, total_idle_cycles, num_nops