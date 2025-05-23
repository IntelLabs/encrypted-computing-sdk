import warnings
from typing import NamedTuple
import networkx as nx

from . import buildVarAccessListFromTopoSort
from assembler.common.config import GlobalConfig
from assembler.common import constants
from assembler.common.cycle_tracking import CycleType
from assembler.common.priority_queue import PriorityQueue
from assembler.common.queue_dict import QueueDict
from assembler.instructions import xinst, cinst, minst
from assembler.memory_model import mem_utilities
from assembler.memory_model import MemoryModel
from assembler.memory_model.variable import Variable, DummyVariable
from assembler.memory_model.register_file import Register, RegisterBank

Constants = constants.Constants

# TODO:
# - Keep instruction being processed into the next bundle if bundle needed to be flushed in mid preparation.
# - Refactor class `Simulation`
#

# TODO:
# Add auto_allocate as configurable?
# --------------------

# FUTURE:
# - Analyze about adding instruction window to dependecy graph creation.
# - Analize about adding terms to priority that will prioritize P-ISA instructions over all others as tie-breaker
#   in simulation priority queue.
#   Maybe add a way to track preparation stage of instructions as part of the priority.
# - Separate variable xinst usage by inputs and outputs to avoid xstoring vars where next usage is a write.
#   May require reorganization and book keeping, look ahead, etc.

auto_allocate = True

class XStoreAssign(xinst.XStore):
    """
    Encapsulates a compound operation of an `xstore` instruction and a
    register assignment.

    This is used for variable eviction from the register file,
    when the register being flushed is needed for a new variable.
    """
    def __init__(self,
                 id: int,
                 src: list,
                 mem_model: MemoryModel,
                 var_target: Variable,
                 dest_spad_addr: int = -1,
                 throughput : int = None,
                 latency : int = None,
                 comment: str = ""):
        """
        Constructs a new `XStoreAssign` object.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.
            src (list): A list containing a single Variable object indicating the source variable to store into SPAD.
                        Variable must be assigned to a register.
                        Variable `spad_address` must be negative (not assigned) or match the address of the corresponding
                        `cstore` instruction.
            mem_model (MemoryModel): The memory model containing the variables.
            var_target (Variable): Variable object that will be allocated in the freed-up register after scheduling the corresponding
                                   `xstore` instruction.
            dest_spad_addr (int, optional): The destination SPAD address. Defaults to -1.
            throughput (int, optional): The throughput of the instruction. Defaults to None.
            latency (int, optional): The latency of the instruction. Defaults to None.
            comment (str, optional): A comment associated with the instruction. Defaults to an empty string.

        Raises:
            ValueError: If `var_target` is an invalid empty or dummy `Variable` object.
        """
        if not var_target or isinstance(var_target, DummyVariable):
            raise ValueError('`var_target`: Invalid empty or dummy `Variable` object.')
        super().__init__(id, src, mem_model, dest_spad_addr, throughput, latency, comment)
        self.__var_target = var_target

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating the timing of executing this instruction.

        The ready cycle for all destinations is updated based on input `cycle_count` and
        this instruction latency. The register is then allocated to the target variable.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.
            schedule_id (int): The schedule identifier.

        Returns:
            int: The throughput for this instruction, i.e., the number of cycles by which to advance
                 the current cycle counter.
        """
        register = self.sources[0].register
        retval = super()._schedule(cycle_count, schedule_id)
        # Perform assignment of register
        register.allocateVariable(self.__var_target)
        return retval

class BundleData(NamedTuple):
    """
    Structure for a completed bundle of instructions.

    Attributes:
        xinsts (list): List of XInstruction objects in the bundle.
        latency (int): Total latency of the bundle.
        latency_from_xstore (int): Bundle latency from the last XStore instruction. This is less than or equal to `latency`.
                                   It is used to track latency before scheduling the next bundle with ifetch more easily,
                                   and to attempt to avoid too many idle cycles.
    """
    xinsts: list
    latency: int
    latency_from_xstore: int

class XWriteCycleTrack(NamedTuple):
    """
    Tracks the cycle where a write occurs to the register file by an XInstruction
    and which banks are being written to.

    Attributes:
        cycle (CycleType): The cycle in which the write happens.
        banks (set): A set of indices of banks being written to in this cycle.
    """
    cycle: CycleType
    banks: set

class CurrentrShuffleTable(NamedTuple):
    """
    Tracks the current rShuffle routing table.

    Attributes:
        r_type (type): The type of rShuffle currently loaded. It can be one of {rShuffle, irShuffle, None}.
        bundle (int): The bundle where the specified r_type was set.
    """
    r_type: type
    bundle: int

class Simulation:
    """
    Simulates the scheduling of instructions in a dependency graph.

    Attributes:
        INSTRUCTION_WINDOW_SIZE (int): The size of the instruction window.
        MIN_INSTRUCTIONS_IN_TOPO_SORT (int): The minimum number of instructions in the topological sort.
        BUNDLE_INSTRUCTION_MIN_LIMIT (int): The minimum number of instructions for a bundle to be considered short.

    Methods:
        addXInstrBackIntoPipeline(xinstr: object):
            Adds an instruction back into the pipeline.
        addXInstrToTopoSort(xinstr_id: tuple):
            Adds an instruction to the topological sort.
        addDependency(new_dependency_instr, original_instr):
            Adds a new dependency instruction to the instruction listing.
        addLiveVar(var_name: str, instr):
            Adds a live variable to the current bundle.
        addUsedVar(var_name: str, instr):
            Removes a used variable from the current bundle.
        appendXInstToBundle(xinstr):
            Appends an XInstruction to the current bundle.
        cleanupPendingWriteCycles():
            Cleans up pending write cycles that have passed.
        canSchedulerShuffle(xinstr) -> CycleType:
            Checks whether the specified xrshuffle XInst can be scheduled now.
        canSchedulerShuffleType(xinstr) -> bool:
            Checks whether the specified rshuffle XInst can be scheduled now.
        canScheduleArithmeticXInstr(xinstr: xinst.XInstruction) -> bool:
            Checks whether the specified XInst can be scheduled now based on the currently loaded metadata.
        findNextInstructionToSchedule() -> object:
            Finds the next instruction to schedule.
        flushBundle():
            Flushes the current bundle.
        flushOutputVariableFromRegister(variable, xinstr = None) -> bool:
            Flushes an output variable from the register.
        generateKeyMaterial(instr_id: int, variable: Variable, register: Register, dep_id = None) -> int:
            Generates key material for the specified variable.
        loadrShuffleRoutingTable(rshuffle_data_type_name: str):
            Queues CInstructions needed to load the `rshuffle` routing table into CE.
        loadBOnesMetadata(spad_addr_offset: int, ones_metadata_segment: int) -> int:
            Queues MInstructions and CInstructions needed to load the Ones metadata.
        loadTwiddleMetadata(spad_addr_offset: int, twid_metadata_segment: int):
            Queues MInstructions and CInstructions needed to load the Twiddle factor generation metadata.
        loadKeygenSeedMetadata(spad_addr_offset: int, kgseed_idx: int) -> int:
            Queues MInstructions and CInstructions needed to load a new keygen seed.
        loadMetadata():
            Loads initial metadata at the start of the program.
        prepareShuffleMetadata(spad_addr_offset: int) -> int:
            Queues MInstructions needed to load the `rshuffle` metadata into SPAD.
        priority_queue_push(xinstr, tie_breaker = None):
            Adds a new instruction to the priority queue.
        priority_queue_remove(xinstr):
            Removes an instruction from the priority queue.
        queueCSyncmLoad(instr_id: int, source_spad_addr: int):
            Checks if needed, and, if so, queues a CSyncm CInstruction to sync to SPAD access from HBM.
        queueMLoad(instr_id: int, target_spad_addr: int, variable, comment = ""):
            Generates instructions to copy from HBM into SPAD.
        queueMSynccLoad(instr_id: int, target_spad_addr: int):
            Checks if needed, and, if so, queues an MSyncc MInstruction to sync to SPAD access.
        updateQueuesSyncsPass2():
            Updates the msyncc and csyncm to correct instruction index after the scheduling completes.
        updateSchedule(instr) -> bool:
            Updates the simulation pending schedule after `instr` has been scheduled.
    """

    INSTRUCTION_WINDOW_SIZE = 100
    MIN_INSTRUCTIONS_IN_TOPO_SORT = 10
    # Amount of instructions for a bundle to be considered short
    BUNDLE_INSTRUCTION_MIN_LIMIT = Constants.MAX_BUNDLE_SIZE // 4 # 10

    def __init__(self,
                 dependency_graph: nx.DiGraph,
                 max_bundle_size: int, # Max number of instructions in a bundle
                 mem_model: MemoryModel,
                 replacement_policy: str,
                 progress_verbose: bool):
        """
        Initializes the simulation of schedule.

        Parameters:
            dependency_graph (nx.DiGraph): The dependency graph of instructions.
            max_bundle_size (int): The maximum number of instructions in a bundle.
            mem_model (MemoryModel): The memory model containing the variables.
            replacement_policy (str): The replacement policy to use.
            progress_verbose (bool): If True, enables verbose progress output.
        """
        assert max_bundle_size == Constants.MAX_BUNDLE_SIZE

        self.__mem_model = mem_model
        self.__replacement_policy = replacement_policy

        self.minsts = []
        self.cinsts = []
        self.xinsts = [] # List of bundles

        # Scheduling vars

        self.current_cycle = CycleType(bundle = len(self.xinsts), cycle = 1)
        self.full_topo_sort = buildVarAccessListFromTopoSort(dependency_graph)
        self.topo_start_idx = 0 # Starting index of the instruction window in full topo_sort
        self.topo_sort = [] # Current slice of topo sort being scheduled
        self.b_topo_sort_changed = True # All changed-tracking flags start as true because scheduling has changed (brought into existence)
        self.dependency_graph = nx.DiGraph(dependency_graph) # Make a copy of the incoming graph to avoid modifying input
        self.b_dependency_graph_changed = True
        # Contains instructions without parent dependencies: sorted list by priority: ready cycle
        # (never edit directly unless absolutely necessary; use priority_queue_remove/push instead)
        self.priority_queue = PriorityQueue()
        self.xstore_pq = PriorityQueue() # Sorted list by priority: ready cycle
        self.b_priority_queue_changed = True # Tracks when there are changes in the priority queue
        self.total_idle_cycles = 0
        # Tracks instructions that are in priority queue or have been removed from graph to avoid encountering
        # if duplicated in the topo sort (instructions are only added to this when extracting them from the topo sort)
        # (instructions that get pushed back into the topo sort for any reason, are removed from this set)
        self.set_extracted_xinstrs = set()

        # Tracks the last xrshuffle scheduled
        # self.last_rshuffle_cycle = CycleType(bundle = -1, cycle = 0)
        self.last_xrshuffle = None

        # Bundle vars

        self.__max_bundle_size = max_bundle_size
        self.b_empty_bundle: bool = False # Tracks if last bundle was empty
        # Tracks if last bundle was flushed with very few instructions
        self.num_short_bundles: int = 0
        # Local dummy variable to be updated per bundle: used to indicate that a register in bank 0 is live
        # for current_cycle.bundle and should not be used by CInsts until next bundle
        self.bundle_dummy_var = DummyVariable(self.current_cycle.bundle)
        # Tracks instructions in current bundle getting constructed
        # (never add to this manually, use appendXInstToBundle() method instead)
        self.xinsts_bundle = []
        self.current_bundle_latency = 0 # Tracks current bundle latency
        self.pre_bundle_csync_minstr = (0, None)
        self.post_bundle_cinsts = []
        # Initial value for live vars (these will always be live)
        self.live_vars_0 = dict()
        # Add meta variables as always live vars:
        # rshuffle routing tables
        if self.mem_model.meta_ntt_aux_table:
            self.live_vars_0[self.mem_model.meta_ntt_aux_table] = None
        if self.mem_model.meta_ntt_routing_table:
            self.live_vars_0[self.mem_model.meta_ntt_routing_table] = None
        if self.mem_model.meta_intt_aux_table:
            self.live_vars_0[self.mem_model.meta_intt_aux_table] = None
        if self.mem_model.meta_intt_routing_table:
            self.live_vars_0[self.mem_model.meta_intt_routing_table] = None
        # Meta ones
        for meta_ones_vars_segment in self.mem_model.meta_ones_vars_segments:
            for meta_ones_var_name in meta_ones_vars_segment:
                self.live_vars_0[meta_ones_var_name] = None
        # Meta twids
        for meta_twid_vars_segment in self.mem_model.meta_twiddle_vars_segments:
            for meta_twid_var_name in meta_twid_vars_segment:
                self.live_vars_0[meta_twid_var_name] = None
        # Tracks live in variable names for current bundle (variables to be used by current bundle)
        self.live_vars: dict = self.live_vars_0 # dict(var_name:str, pending_uses: set(XInstruction))
        self.live_outs = set() # Contains variables being stored in this bundle to avoid reusing them
        # Ordered list of XWriteCycleTrack to track the cycle in which rshuffles are writing.
        # This is used to avoid scheduling instructions that write to these banks on the same cycle as
        # rshuffles.
        self.pending_write_cycles = []

        # Metadata tracking

        # Book-keeping to track keygen metadata

        # Starting SPAD address for keygen seed metadata:
        # this will be overwritten by new keygen seed metadata whenever a swap is needed.
        self.metadata_spad_addr_start_kgseed = -1
        self.bundle_current_kgseed = -1 # Tracks current index of keygen seed metadata loaded
        self.bundle_used_kg_seed = -1 # Tracks the last bundle that used current keygen seed
        self.last_keygen_index = -1 # Tracks the last key material generation index with current seed

        # Book-keeping to track residual metadata

        # Starting SPAD address for ones metadata:
        # this will be overwritten by new ones metadata whenever a swap is needed.
        self.metadata_spad_addr_start_ones = -1
        # Metadata for ones segment `i` supports computation of arithmetic operations
        # with rns in range `[i * 64, (i + 1) * 64)`
        # i == -1 means uninitialized
        self.bundle_current_ones_segment = -1 # Tracks current ones segment metadata loaded
        self.bundle_needed_ones_segment = -1 # Signals the ones segment metadata needed

        # Starting SPAD address for twid metadata:
        # this will be overwritten by new twid metadata whenever a swap is needed.
        self.metadata_spad_addr_start_twid = -1
        # Metadata for twiddles segment `i` supports computation of twiddle factors
        # with rns in range `[i * 64, (i + 1) * 64)`
        # i == -1 means uninitialized
        self.bundle_current_twid_segment = -1 # Tracks current twid segment metadata loaded
        self.bundle_needed_twid_segment = -1 # Signals the twid segment metadata needed

        # Book-keeping to track that rShuffle and irShuffle don't mix in the same bundle

        # Tracks the current type of rshuffle supported (rShuffle, irShuffle, None),
        # and what bundle was it last set
        self.bundle_current_rshuffle_type = (None, 0) # (type: {rShuffle, irShuffle, None}, bundle: int)
        self.bundle_needed_rshuffle_type = None # Type of last rshuffle {rShuffle, irShuffle, None} scheduled in current bundle

        # xinstfetch vars

        self.xinstfetch_hbm_addr = 0
        self.xinstfetch_xq_addr = 0
        self.__max_bundles_per_xinstfetch = Constants.WORD_SIZE / (self.max_bundle_size * Constants.XINSTRUCTION_SIZE_BYTES)
        self.xinstfetch_cinsts_buffer = [] # Used to group all xinstfetch per capacity of XInst queue
        self.xinstfetch_location_idx_in_cinsts = 0 # Location in cinst where to insert xinstfetch's when a group is completed

        # Progress report vars

        # Tracks the number of instruction (in original dependency graph) that have been scheduled
        self.scheduled_xinsts_count = 0
        self.verbose = progress_verbose

    @property
    def last_xinstr(self) -> object:
        """
        Provides the last XInstruction in the current bundle or the last bundle with instructions.

        Returns:
            object: The last XInstruction or None if no instructions are found.
        """
        retval = None
        if len(self.xinsts_bundle) > 0:
            retval = self.xinsts_bundle[-1]
        elif len(self.xinsts) > 0:
            # Find the last bundle with instructions
            # (this should be the last bundle in the list of bundles)
            for bundle in reversed(self.xinsts):
                if len(bundle) > 0:
                    # Return last instruction in bundle
                    retval = bundle[-1]
                    break
        return retval

    @property
    def max_bundle_size(self) -> int:
        """
        Provides the maximum bundle size.

        Returns:
            int: The maximum bundle size.
        """
        return self.__max_bundle_size

    @property
    def max_bundles_per_xinstfetch(self) -> int:
        """
        Provides the maximum number of bundles per xinstfetch.

        Returns:
            int: The maximum number of bundles per xinstfetch.
        """
        return self.__max_bundles_per_xinstfetch

    @property
    def mem_model(self) -> str:
        """
        Provides the memory model.

        Returns:
            str: The memory model.
        """
        return self.__mem_model

    @property
    def progress_pct(self) -> float:
        """
        Provides the progress percentage.

        Returns:
            float: The progress percentage.
        """
        return self.scheduled_xinsts_count * 100.0 / self.total_instructions

    @property
    def replacement_policy(self) -> str:
        """
        Provides the replacement policy.

        Returns:
            str: The replacement policy.
        """
        return self.__replacement_policy

    @property
    def total_instructions(self) -> int:
        """
        Provides the total number of instructions.

        Returns:
            int: The total number of instructions.
        """
        return self.dependency_graph.number_of_nodes() + self.scheduled_xinsts_count

    def addXInstrBackIntoPipeline(self, xinstr: object):
        """
        Adds an instruction back into the pipeline.

        Parameters:
            xinstr (object): The instruction to add back into the pipeline.

        Raises:
            ValueError: If `xinstr` is a `Move` instruction or is already scheduled.
        """
        if isinstance(xinstr, xinst.Move):
            raise ValueError('`xinstr` is a `Move` instruction. `Move` instructions cannot be inserted into the pipeline.')
        if xinstr.is_scheduled:
            raise ValueError('`xinstr` already scheduled.')
        assert xinstr.id in self.dependency_graph
        if self.dependency_graph.in_degree(xinstr.id) > 0:
            if xinstr in self.priority_queue:
                # Remove from priority queue because it now has a dependency
                self.priority_queue_remove(xinstr)
            # Add back to topo sort because we have new dependencies
            self.addXInstrToTopoSort(xinstr.id)
        else:
            # Original instruction has no dependencies, so, put it back in priority queue
            self.priority_queue_push(xinstr)

        # Remove instruction vars from live list since it's being demoted.
        # Pending xstore variables must be kept alive to avoid attempts to flush them again.
        if not isinstance(xinstr, xinst.XStore):
            for v in xinstr.sources + xinstr.dests:
                if isinstance(v, Variable) \
                   and v.name in self.live_vars \
                   and xinstr in self.live_vars[v.name]:
                    self.addUsedVar(v.name, xinstr)

    def addXInstrToTopoSort(self, xinstr_id: tuple):
        """
        Adds an instruction to the topological sort.

        Parameters:
            xinstr_id (tuple): The ID of the instruction to add.

        Raises:
            ValueError: If `xinstr_id` is not part of the dependency graph or is in the priority queue.
        """
        if xinstr_id not in self.dependency_graph:
            raise ValueError("`xinstr_id`: cannot add an instruction to topo sort that is not part of the dependency graph.")
        if xinstr_id in self.priority_queue:
            # Adding back to topo sort, xinstr cannot be in priority queue
            raise ValueError("`xinstr_id`: cannot be in priority queue.")
        # Find position in topo sort
        target_idx = len(self.topo_sort)
        match_idxs = [] # Locations where the same xinstr was found in topo sort
        for idx, topo_instr_id in enumerate(self.topo_sort):
            if topo_instr_id == xinstr_id:
                match_idxs.append(idx)
            elif topo_instr_id in self.dependency_graph \
               and self.dependency_graph.in_degree(topo_instr_id) >= self.dependency_graph.in_degree(xinstr_id):
                target_idx = idx
                break
        self.topo_sort = self.topo_sort[:target_idx] + [ xinstr_id ] + self.topo_sort[target_idx:]
        # Remove the previous instances found of xinstr from topo sort as it has incorrect order now
        for idx, match_idx in enumerate(match_idxs):
            del self.topo_sort[match_idx - idx]
        self.b_topo_sort_changed = True
        self.set_extracted_xinstrs.discard(xinstr_id)

    def addDependency(self,
                      new_dependency_instr,
                      original_instr):
        """
        Adds `new_dependency_instr` to the instruction listing as a new dependency of
        `original_instr`.

        Dependency graph and topo sort are updated as appropriate. `new_dependency_instr` is NOT
        added to the topo_sort.

        Variables in sources and dests for `new_dependency_instr` are added to `live_vars`.

        Parameters:
            new_dependency_instr: The new dependency instruction to add.
            original_instr: The original instruction to which the new dependency is added.
        """
        # Add new instruction to instructions listing (in dependency graph)
        self.dependency_graph.add_node(new_dependency_instr.id, instruction=new_dependency_instr)
        self.b_dependency_graph_changed = True
        if original_instr:
            assert original_instr.id in self.dependency_graph
            self.dependency_graph.add_edge(new_dependency_instr.id, original_instr.id) # Link as dependency to input instruction
            self.addXInstrBackIntoPipeline(original_instr)

        all_vars = set(v for v in new_dependency_instr.sources + new_dependency_instr.dests \
                            if isinstance(v, Variable) and not isinstance(v, DummyVariable))
        for v in all_vars:
            # Add dependencies to all other instructions
            deps_added = 0
            for idx, next_instr_id in v.accessed_by_xinsts:
                if idx > self.topo_start_idx + 2 * Simulation.INSTRUCTION_WINDOW_SIZE:
                    # Only add dependencies within the instruction window and next 2 instruction windows
                    if deps_added > 0 or len(v.accessed_by_xinsts) <= 0:
                        # Add, at least, one dependency if needed
                        break
                if next_instr_id != new_dependency_instr.id:
                    assert next_instr_id in self.dependency_graph
                    self.dependency_graph.add_edge(new_dependency_instr.id, next_instr_id) # Link as dependency to input instruction
                    if self.dependency_graph.in_degree(next_instr_id) == 1:
                        # We need to add next instruction back to topo sort because it will have a dependency
                        next_instr = self.dependency_graph.nodes[next_instr_id]['instruction']
                        self.addXInstrBackIntoPipeline(next_instr)
                    deps_added += 1
            self.addLiveVar(v.name, new_dependency_instr) # Source and dests variables are now a live-in for new_dependency_instr

    def addLiveVar(self,
                   var_name: str,
                   instr):
        """
        Adds a live variable to the current bundle.

        Parameters:
            var_name (str): The name of the variable to add.
            instr: The instruction associated with the variable.
        """
        if var_name not in self.live_vars:
            self.live_vars[var_name] = set()
        self.live_vars[var_name].add(instr)

    def addUsedVar(self,
                   var_name: str,
                   instr):
        """
        Removes a used variable from the current bundle.

        Parameters:
            var_name (str): The name of the variable to remove.
            instr: The instruction associated with the variable.
        """
        self.live_vars[var_name].remove(instr)
        if len(self.live_vars[var_name]) <= 0:
            self.live_vars.pop(var_name)

    def appendXInstToBundle(self, xinstr):
        """
        Appends an XInstruction to the current bundle.

        Parameters:
            xinstr: The XInstruction to append.

        Raises:
            ValueError: If `xinstr` is None.
            AssertionError: If the bundle is already full.
        """
        if not xinstr:
            raise ValueError('`xinstr` cannot be `None`.')
        assert len(self.xinsts_bundle) < self.max_bundle_size, 'Cannot append XInstruction to full bundle.'
        self.xinsts_bundle.append(xinstr)
        if self.current_bundle_latency < self.current_cycle.cycle + xinstr.latency:
            self.current_bundle_latency = self.current_cycle.cycle + xinstr.latency

    def cleanupPendingWriteCycles(self):
        """
        Cleans up pending write cycles that have passed.
        """
        # Remove any write cycles that passed
        front_write_cycle_idx = -1 # len(self.pending_write_cycles)
        for idx, write_cycle in enumerate(self.pending_write_cycles):
            if write_cycle.cycle < self.current_cycle: # Not <= because no instruction writes on its decoding (first) cycle
                # Found first write cycle in the list that occurs after current cycle
                front_write_cycle_idx = idx
                break
        self.pending_write_cycles = self.pending_write_cycles[front_write_cycle_idx + 1:]

    def canSchedulerShuffle(self, xinstr) -> CycleType:
        """
        Checks whether the specified xrshuffle XInst can be scheduled now,
        based on the special latency timing.

        Returns:
            CycleType: The cycle where the specified instruction can be scheduled:
                - Returns cycle <= current_cycle if instruction can be scheduled now.
                - Returns cycle > current_cycle the cycle where the instruction can be scheduled.
                  If instruction is an xrshuffle, this takes into account the slotting rule.
        """
        # This is used to check whether an rshuffle is in the slotted latency from
        # the previous rshuffle, or outside of the special latency.

        instr_ready_cycle = max(xinstr.cycle_ready, self.current_cycle)

        retval = instr_ready_cycle

        if xinstr.cycle_ready.bundle <= self.current_cycle.bundle \
           and self.last_xrshuffle is not None \
           and isinstance(xinstr, (xinst.rShuffle, xinst.irShuffle)):
            # Attempting to schedule an rshuffle after a previous one already got
            # scheduled in the same bundle

            last_rshuffle_cycle = self.last_xrshuffle.schedule_timing.cycle
            assert self.current_cycle.bundle >= last_rshuffle_cycle.bundle, \
                "Last scheduled rshuffle cannot be in the future."

            if self.current_cycle.bundle == last_rshuffle_cycle.bundle:
                # Last scheduled rshuffle was in this bundle
                cycle_delta = abs(instr_ready_cycle.cycle - last_rshuffle_cycle.cycle)
                if (isinstance(xinstr, xinst.rShuffle) and isinstance(self.last_xrshuffle, xinst.rShuffle)) \
                   or (isinstance(xinstr, xinst.irShuffle) and isinstance(self.last_xrshuffle, xinst.irShuffle)):
                    # New rshuffle and previous are of the same kind
                    if cycle_delta < self.last_xrshuffle.SpecialLatencyMax:
                        # Trying to schedule within max special latency: attempt to slot
                        r = cycle_delta % self.last_xrshuffle.SpecialLatencyIncrement
                        cycle_delta += ((0 if r == 0 else self.last_xrshuffle.SpecialLatencyIncrement) - r)
                        if cycle_delta >= self.last_xrshuffle.SpecialLatencyMax:
                            # Slot found is greater than max latency, so, we can schedule at max latency
                            cycle_delta = self.last_xrshuffle.SpecialLatencyMax
                        retval = CycleType(bundle = self.current_cycle.bundle,
                                           cycle = last_rshuffle_cycle.cycle + cycle_delta)
                else:
                    # New rshuffle and previous are inverse: only schedule outside
                    # of the full latency
                    retval = CycleType(bundle = self.current_cycle.bundle,
                                       cycle = max(self.current_cycle.cycle, last_rshuffle_cycle.cycle + self.last_xrshuffle.latency))

        if retval < instr_ready_cycle:
            retval = instr_ready_cycle

        return retval

    def canSchedulerShuffleType(self, xinstr) -> bool:
        """
        Checks whether the specified rshuffle XInst can be scheduled now,
        or if there are inverse rshuffles in queue that can be scheduled because
        the currently loaded routing table matches them instead.

        Returns:
            bool: True if the specified instruction is an xrshuffle that can be scheduled in
                  this bundle, or specified instruction is not an xrshuffle. False otherwise.

        This is used to avoid switching tables back and forth while there
        are still xrshuffles of correct table type pending.
        """
        retval = True

        if isinstance(xinstr, (xinst.rShuffle, xinst.irShuffle)):
            # Check if a routing table change is needed for specified rshuffle

            # Can schedule if not on this bundle, or is instance of previously scheduled
            # rshuffles in this bundle
            retval = xinstr.cycle_ready.bundle > self.current_cycle.bundle \
                     or self.bundle_needed_rshuffle_type is None \
                        or isinstance(xinstr, self.bundle_needed_rshuffle_type)

            if self.bundle_current_rshuffle_type[0] is not None \
               and not isinstance(xinstr, self.bundle_current_rshuffle_type[0]) \
               and retval:
                # Routing table change will be needed if we want to schedule specified xrshuffle

                # Search priority queue to see if there are any rshuffles matching
                # current routing tables that can be queued instead
                # NOTE: Traversing a priority queue is not good practice because we should not be
                # messing with its contents, but it is needed for the single type
                # of rshuffle per bundle restriction.

                retval = next((False for _, inv_rshuffle in self.priority_queue \
                               if isinstance(inv_rshuffle, self.bundle_current_rshuffle_type[0]) \
                                  and inv_rshuffle.cycle_ready.bundle <= self.current_cycle.bundle),
                               retval)

            assert not retval \
                   or xinstr.cycle_ready.bundle > self.current_cycle.bundle \
                   or self.bundle_needed_rshuffle_type is None or isinstance(xinstr, self.bundle_needed_rshuffle_type), \
                   f'Found rshuffle of type {type(xinstr)}, but type {self.bundle_needed_rshuffle_type} already scheduled in bundle.'

        return retval

    def canScheduleArithmeticXInstr(self, xinstr: xinst.XInstruction) -> bool:
        """
        Checks whether the specified XInst can be scheduled now based on
        the currently loaded metadata.

        Returns:
            bool: True if the specified XInst can be scheduled in this bundle (may require
                  change of metadata). False otherwise.

        This is used to avoid switching metadata back and forth while there
        are still XInsts of current metadata pending.
        """
        retval = True

        if xinstr.res is not None:
            # Instruction has residual

            assert self.bundle_current_ones_segment == self.bundle_current_twid_segment, \
                'Current Ones and Twiddle metadata segments are not synchronized.'
            assert self.bundle_needed_ones_segment == self.bundle_needed_twid_segment, \
                'Needed Ones and Twiddle metadata segments are not synchronized.'

            xinstr_required_segment = xinstr.res // constants.MemoryModel.MAX_RESIDUALS
            # Can schedule if not on this bundle, or required residual segment
            # is same as previously scheduled in this bundle
            retval = xinstr.cycle_ready.bundle > self.current_cycle.bundle \
                     or self.bundle_needed_ones_segment == -1 \
                     or self.bundle_needed_ones_segment == xinstr_required_segment

            # Check if a metadata change is needed for specified XInst
            if self.bundle_current_ones_segment != -1 \
               and self.bundle_current_ones_segment != xinstr_required_segment \
               and retval:
                # Metadata change will be needed if we want to schedule specified XInst

                # Search priority queue to see if there are any arithmetic instructions matching
                # current metadata that can be queued instead
                # NOTE: Traversing a priority queue is not good practice because we should
                # not be messing with its contents, but it is needed for the single
                # metadata segment per bundle restriction.
                retval = next((False for _, other_xinstr in self.priority_queue \
                               if other_xinstr.res is not None \
                                  and other_xinstr.res // constants.MemoryModel.MAX_RESIDUALS == self.bundle_current_ones_segment \
                                  and other_xinstr.cycle_ready.bundle <= self.current_cycle.bundle),
                               retval)

            assert not retval \
                   or xinstr.cycle_ready.bundle > self.current_cycle.bundle \
                   or self.bundle_needed_ones_segment == -1 or xinstr_required_segment == self.bundle_needed_ones_segment, \
                   f'Found XInst of residual segment {xinstr_required_segment}, but segment {self.bundle_needed_ones_segment} already scheduled in bundle.'

        return retval

    def findNextInstructionToSchedule(self) -> object:
        """
        Finds the next instruction to schedule.

        Returns:
            object: The next instruction to schedule or None if priority_queue is empty.

            Returned instruction may be an injected xexit if no instructions are left to be
            scheduled for current bundle.
        """
        retval = None

        if self.priority_queue:
            while retval is None \
                  and self.priority_queue.peek()[1].cycle_ready.bundle <= self.current_cycle.bundle:
                # Check if there is any immediate instruction we can schedule
                # in this cycle
                immediate_instr = self.priority_queue.find(self.current_cycle)
                while retval is None and immediate_instr is not None:
                    # Check found instruction has correct priority
                    if immediate_instr.cycle_ready == self.current_cycle:
                        # Check for write cycle conflicts
                        if hasBankWriteConflict(immediate_instr, self):
                            # Write cycle conflict found, so, update found instruction cycle ready
                            new_cycle_ready = CycleType(bundle = self.current_cycle.bundle,
                                                        cycle = max(immediate_instr.cycle_ready.cycle, self.current_cycle.cycle) + 1)
                            immediate_instr.cycle_ready = new_cycle_ready
                        else:
                            new_cycle_ready = self.canSchedulerShuffle(immediate_instr)
                            if immediate_instr.cycle_ready != new_cycle_ready:
                                # Only xrshuffles should have a changed cycle ready if slotted
                                # and got picked outside of a slot to schedule.
                                assert immediate_instr.cycle_ready < new_cycle_ready, \
                                    "Computed new cycle ready cannot be earlier than instruction's cycle ready."
                                immediate_instr.cycle_ready = new_cycle_ready # Update instruction's cycle ready
                            else:
                                # Found immediate instruction
                                self.priority_queue_remove(immediate_instr)
                                retval = immediate_instr
                    if not retval:
                        # Found instruction that has incorrect priority, so, correct it
                        self.priority_queue_push(immediate_instr)
                        # See if there is any other immediate instruction we can schedule
                        immediate_instr = self.priority_queue.find(self.current_cycle)

                # If no immediate instruction found:
                # Find the first we can schedule
                while retval is None:
                    priority, p_inst = self.priority_queue.peek()
                    if p_inst.cycle_ready.bundle < self.current_cycle.bundle:
                        # Correct instruction ready cycle to this bundle
                        p_inst.cycle_ready = CycleType(bundle = self.current_cycle.bundle,
                                                       cycle = 0)
                    # Check found instruction has correct priority
                    if p_inst.cycle_ready == priority:
                        # Check for write cycle conflicts
                        if hasBankWriteConflict(p_inst, self):
                            # Write cycle conflict found, so, update found instruction cycle ready
                            new_cycle_ready = CycleType(bundle = self.current_cycle.bundle,
                                                        cycle = max(p_inst.cycle_ready.cycle, self.current_cycle.cycle) + 1)
                            p_inst.cycle_ready = new_cycle_ready
                        else:
                            new_cycle_ready = self.canSchedulerShuffle(p_inst)
                            if p_inst.cycle_ready != new_cycle_ready:
                                # Only xrshuffles should have a changed cycle ready if slotted
                                # and got picked outside of a slot to schedule.
                                assert p_inst.cycle_ready < new_cycle_ready, \
                                    "Computed new cycle ready cannot be earlier than instruction's cycle ready."
                                p_inst.cycle_ready = new_cycle_ready # Update instruction's cycle ready
                            else:
                                # Found instruction to schedule at the head of queue
                                priority, retval = self.priority_queue.pop()
                                assert(retval.id == p_inst.id and priority == retval.cycle_ready)
                    if not retval:
                        # Found instruction that has incorrect priority, so, correct it
                        # (this may change its order in the priority queue)
                        self.priority_queue_push(p_inst)

                assert(retval)

                if not self.canSchedulerShuffleType(retval):
                    # Found rshuffle that requires routing table change, but other
                    # rshuffles with current routing table still available:
                    # Move rshuffle to next bundle
                    retval.cycle_ready = CycleType(bundle = self.current_cycle.bundle + 1,
                                                   cycle = 0)
                    # Put back in priority queue
                    self.priority_queue_push(retval)
                    retval = None # Continue looping to find another suitable instruction

                if retval and not self.canScheduleArithmeticXInstr(retval):
                    # Found XInst that requires metadata change, but other
                    # XInst with current metadata still available:
                    # Move XInst to next bundle
                    retval.cycle_ready = CycleType(bundle = self.current_cycle.bundle + 1,
                                                   cycle = 0)
                    # Put back in priority queue
                    self.priority_queue_push(retval)
                    retval = None # Continue looping to find another suitable instruction

        return retval

    def flushBundle(self):
        """
        Flushes the current bundle.

        Raises:
            RuntimeError: If the previous bundle was short and the current bundle is empty.
        """
        if self.b_empty_bundle and len(self.xinsts_bundle) <= 0:
            # Previous bundle was short
            raise RuntimeError('Cannot flush an empty bundle.')

        self.b_empty_bundle = len(self.xinsts_bundle) <= 0 # Flag whether this is an empty bundle
        # Flag if this is a short bundle
        if len(self.xinsts_bundle) <= self.BUNDLE_INSTRUCTION_MIN_LIMIT:
            self.num_short_bundles += 1
        else:
            self.num_short_bundles = 0

        # Complete the bundle

        instr = None
        if len(self.xinsts_bundle) < self.max_bundle_size:
            # Bundle not full:
            # Schedule an exit bundle
            tmp_comment = f" terminating bundle {self.current_cycle.bundle}"
            if self.num_short_bundles > 0:
                tmp_comment += ": short bundle"
            instr = xinst.Exit(len(self.xinsts), comment=tmp_comment)
            self.current_cycle += instr.schedule(self.current_cycle, len(self.xinsts_bundle) + 1)
            self.appendXInstToBundle(instr)

        # Find bundle latency measurements before padding bundle
        assert(not isinstance(self.xinsts_bundle[-1], xinst.Nop)) # Last instruction in bundle is not a nop
        bundle_latency = self.current_bundle_latency
        # Find last xstore in bundle
        bundle_last_xstore = next((self.xinsts_bundle[idx] for idx in reversed(range(len(self.xinsts_bundle))) \
                                   if isinstance(self.xinsts_bundle[idx], xinst.XStore)),
                                  None)
        # Latency from last xstore is the total bundle latency minus the cycle where the xstore was scheduled:
        # Measured from the cycle where last xstore was scheduled to the total latency
        bundle_latency_from_last_xstore = (bundle_latency - bundle_last_xstore.schedule_timing.cycle.cycle) \
                                          if bundle_last_xstore \
                                          else bundle_latency
        if bundle_latency_from_last_xstore < 0:
            bundle_latency_from_last_xstore = 0

        if not instr:
            _, instr = self.priority_queue.peek() if len(self.priority_queue) > 0 else (0, self.xinsts_bundle[-1])
        for _ in range(self.max_bundle_size - len(self.xinsts_bundle)):
            # Pad incomplete bundle with nops:
            # Incomplete bundles are finished by an xexit, but need to be padded to max_bundle_size
            b_scheduled = scheduleXNOP(instr,
                                       1, # Idle cycles
                                       self,
                                       force_nop=True) # We want nop to be added regardless of last in bundle
            assert(b_scheduled)

        assert(len(self.xinsts_bundle) == self.max_bundle_size)

        # See if we need to sync to MInstQ before fetching bundle
        if self.pre_bundle_csync_minstr[1]:
            minstr = self.pre_bundle_csync_minstr[1]
            assert(minstr.is_scheduled)
            csyncm = cinst.CSyncm(minstr.id[0], minstr)
            csyncm.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(csyncm)
        self.pre_bundle_csync_minstr = (0, None) # Clear sync because we may not need in next bundle

        # Schedule the bundle fetch
        ifetch = cinst.IFetch(self.xinsts_bundle[0].id[1], # ID of first instruction in bundle, just for book-keeping
                              self.current_cycle.bundle)

        # See if we need idle CInstQ cycles from previous bundle before ifetch this bundle
        if len(self.xinsts) > 0:
            # Find latency for the CInstQ since last cstore (or ifetch if not cstore)
            idx = len(self.cinsts) - 1
            cq_throughput = 0
            while idx >= 0 \
                and not isinstance(self.cinsts[idx], (cinst.IFetch, cinst.CStore)):
                cq_throughput += self.cinsts[idx].throughput
                idx -= 1

            # Added ifetch latency to avoid timing errors when bundles are short or empty
            idle_c_cycles = self.xinsts[-1].latency_from_xstore - cq_throughput \
                            + ifetch.latency
            if idle_c_cycles > 0:
                cnop = cinst.CNop(self.current_cycle.bundle, idle_c_cycles)
                cnop.schedule(self.current_cycle, len(self.cinsts) + 1)
                self.cinsts.append(cnop)

        # See if we need to load a new rshuffle routing table
        # (not counted in the nops before next bundle because we don't want to
        # switch routing tables in mid rshuffle if it is still in flight)
        if self.bundle_needed_rshuffle_type is not None \
           and self.bundle_current_rshuffle_type[0] != self.bundle_needed_rshuffle_type:
            self.loadrShuffleRoutingTable(self.bundle_needed_rshuffle_type.RSHUFFLE_DATA_TYPE)
            self.bundle_current_rshuffle_type = (self.bundle_needed_rshuffle_type, self.current_cycle.bundle)

        # See if we need to load new twid metadata
        # (not counted in the nops before next bundle because we don't want to
        # switch twid metadata in mid bundle if it is still in flight)
        if self.bundle_needed_twid_segment >= 0 \
           and self.bundle_current_twid_segment != self.bundle_needed_twid_segment:
            self.loadTwiddleMetadata(self.metadata_spad_addr_start_twid, self.bundle_needed_twid_segment)
            self.bundle_current_twid_segment = self.bundle_needed_twid_segment

        # See if we need to load new ones metadata
        # (not counted in the nops before next bundle because we don't want to
        # switch ones metadata in mid bundle if it is still in flight)
        if self.bundle_needed_ones_segment >= 0 \
           and self.bundle_current_ones_segment != self.bundle_needed_ones_segment:
            self.loadBOnesMetadata(self.metadata_spad_addr_start_ones, self.bundle_needed_ones_segment)
            self.bundle_current_ones_segment = self.bundle_needed_ones_segment

        ifetch.schedule(self.current_cycle, len(self.cinsts) + 1)
        self.cinsts.append(ifetch)

        # Add bundle to list of bundles
        self.xinsts.append(BundleData(xinsts=self.xinsts_bundle,
                                      latency=bundle_latency,
                                      latency_from_xstore=bundle_latency_from_last_xstore))

        # Schedule all the pending CInsts
        for idx, cstore_instr in enumerate(self.post_bundle_cinsts):
            var_name, (variable, dst_spad_addr) = self.mem_model.store_buffer.peek()
            cstore_instr.schedule(self.current_cycle, len(self.cinsts) + idx + 1)

            # Check if this is an output variable which is done
            if variable.name in self.mem_model.output_variables \
               and not variable.accessed_by_xinsts:
                # Variable is output and it is not used anymore
                # Sync to last CInst access to avoid storing before access completes
                assert(self.mem_model.spad.getAccessTracking(dst_spad_addr).last_cstore[1] == cstore_instr)
                msyncc = minst.MSyncc(cstore_instr.id[0],
                                      cstore_instr)
                msyncc.schedule(self.current_cycle, len(self.minsts) + 1)
                self.minsts.append(msyncc)
                dest_hbm_addr = variable.hbm_address
                if dest_hbm_addr < 0:
                    if not auto_allocate:
                        raise RuntimeError(f"Variable {variable.name} not found in HBM.")
                    dest_hbm_addr = self.mem_model.hbm.findAvailableAddress(self.mem_model.output_variables)
                    if dest_hbm_addr < 0:
                        raise RuntimeError("Out of HBM space.")
                mstore = minst.MStore(cstore_instr.id[0],
                                      [ variable ],
                                      self.mem_model,
                                      dest_hbm_addr,
                                      comment=(' id: {} - flushing').format(cstore_instr.id))
                mstore.schedule(self.current_cycle, len(self.minsts) + 1)
                self.minsts.append(mstore)

        self.cinsts += self.post_bundle_cinsts

        # Clean up for next bundle

        self.current_bundle_latency = 0
        self.xinsts_bundle          = []
        self.post_bundle_cinsts     = []
        self.pending_write_cycles   = []
        self.live_outs              = set()

        self.bundle_needed_rshuffle_type = None
        self.bundle_needed_ones_segment  = -1
        self.bundle_needed_twid_segment  = -1

        # Reset all global cycle trackings
        for xinstr_type in xinst.GLOBAL_CYCLE_TRACKING_INSTRUCTIONS:
            xinstr_type.reset_GlobalCycleReady()

        # Free up bank 0 registers with stale dummy variables
        # (dummies left as placeholders in bank 0 by previous bundles)
        for idx in range(len(self.mem_model.register_banks)):
            bank = self.mem_model.register_banks[idx]
            for reg in bank:
                if isinstance(reg.contained_variable, DummyVariable) \
                   and reg.contained_variable.tag < self.current_cycle.bundle:
                    # Register was used more than a bundle ago and can be re-used
                    reg.allocateVariable(None)

        self.b_dependency_graph_changed = True
        # Next bundle starts
        assert(len(self.xinsts) == self.current_cycle.bundle + 1)
        self.current_cycle = CycleType(bundle = len(self.xinsts), cycle = 1)
        self.bundle_dummy_var = DummyVariable(self.current_cycle.bundle) # Dummy variable for new bundle

    def flushOutputVariableFromRegister(self,
                                        variable,
                                        xinstr = None) -> bool:
        """
        Flushes an output variable from the register.

        Parameters:
            variable: The variable to flush.
            xinstr (optional): The instruction associated with the variable. Defaults to None.

        Returns:
            bool: True if the variable was successfully flushed, or it didn't need flushing.

        Raises:
            ValueError: If `xinstr` is None when there are no other XInstructions available in the listing.
        """
        retval = True

        if not xinstr:
            xinstr = self.last_xinstr
        if not xinstr:
            raise ValueError('`xinstr`: cannot be None when there are no other XInstructions available in the listing.')
        if variable.register_dirty:
            # Variable is in a dirty register:
            # Flush the register

            # Find a location in SPAD
            dest_spad_addr = variable.spad_address
            if dest_spad_addr < 0:
                dest_spad_addr = findSPADAddress(xinstr, self)
            if dest_spad_addr < 0:
                retval = False # No SPAD available, flush later

            if retval:
                xstore = _createXStore(xinstr.id[0],
                                        dest_spad_addr,
                                        variable,
                                        None,
                                        ' flushing output',
                                        self)
                self.addDependency(xstore, None)
                # Add to topo_sort
                self.addXInstrToTopoSort(xstore.id)
        return retval

    def generateKeyMaterial(self,
                            instr_id: int,
                            variable: Variable,
                            register: Register,
                            dep_id = None) -> int:
        """
        Generates key material for the specified variable.

        Parameters:
            instr_id (int): The ID of the instruction.
            variable (Variable): The variable for which to generate key material.
            register (Register): The register associated with the variable.
            dep_id (optional): The dependency ID. Defaults to None.

        Returns:
            int: 1 if good to go, 2 if leave for next bundle (could not generate key material).

        Raises:
            ValueError: If the variable is not keygen.
            RuntimeError: If the keygen variable has already been generated or if the keygen variable generation is out of order.
        """
        # Key material cannot be generated if it requires a seed change, but current seed
        # was already used in this bundle.

        retval = 1

        if variable.name not in self.mem_model.keygen_variables:
            raise ValueError('Variable "{}" is not keygen.'.format(variable.name))
        if self.mem_model.isVarInMem(variable.name):
            raise RuntimeError('Keygen variable "{}" has already been generated.'.format(variable.name))

        seed_idx, key_idx = self.mem_model.keygen_variables[variable.name]

        # Check the seed
        if seed_idx != self.bundle_current_kgseed:
            if self.bundle_used_kg_seed >= self.current_cycle.bundle:
                # Current seed already used in this bundle: cannot change seeds
                retval = 2
            else:
                # Change seed to needed
                self.loadKeygenSeedMetadata(self.metadata_spad_addr_start_kgseed, seed_idx)

        if retval == 1:
            # Seed ready to be used to generate new key material

            if key_idx != self.last_keygen_index + 1:
                raise RuntimeError(('Keygen variable "{}" generation out of order. '
                                    'Expected key index {}, but received {} for seed {}.').format(variable.name,
                                                                                                  self.last_keygen_index + 1,
                                                                                                  key_idx,
                                                                                                  self.bundle_current_kgseed))

            comment = "" if dep_id is None else 'dep id: {}'.format(dep_id)
            kg_load = cinst.KGLoad(instr_id, register, [ variable ], comment=comment)
            # Nop required because kg_load/kg_start instructions have a resource dependency among them
            cnop = cinst.CNop(instr_id,
                              kg_load.latency,
                              comment='kg_load {} wait period'.format(kg_load.id))
            cnop.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(cnop)

            kg_load.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(kg_load)

            # Seed used this bundle
            self.bundle_used_kg_seed = self.current_cycle.bundle
            self.last_keygen_index = key_idx # Advance the last generated index tracker

        return retval

    def loadrShuffleRoutingTable(self,
                                 rshuffle_data_type_name: str):
        """
        Queues CInstructions needed to load the `rshuffle` routing table into CE.

        Parameters:
            rshuffle_data_type_name (str): One of { 'ntt', 'intt' }.

        Raises:
            ValueError: If `rshuffle_data_type_name` is invalid.
            RuntimeError: If the required routing table for the specified type is not present in metadata.
        """
        # Select the correct targets based on rshuffle or irshuffle
        RegisterTargets = constants.MemInfo.MetaTargets
        aux_table_name = ""
        aux_table_target = -1
        routing_table_name = ""
        routing_table_target = -1
        if rshuffle_data_type_name == xinst.rShuffle.RSHUFFLE_DATA_TYPE:
            aux_table_name     = self.mem_model.meta_ntt_aux_table
            routing_table_name = self.mem_model.meta_ntt_routing_table
        elif rshuffle_data_type_name == xinst.irShuffle.RSHUFFLE_DATA_TYPE:
            aux_table_name     = self.mem_model.meta_intt_aux_table
            routing_table_name = self.mem_model.meta_intt_routing_table
        else:
            raise ValueError(('`rshuffle_data_type_name`: invalid value "{}". Expected one of {}.').format(rshuffle_data_type_name,
                                                                                                      { xinst.rShuffle.RSHUFFLE_DATA_TYPE,
                                                                                                        xinst.irShuffle.RSHUFFLE_DATA_TYPE }))
        # Only NTT targets are supported for both NTT and iNTT in RTL 0.9
        aux_table_target     = RegisterTargets.TARGET_NTT_AUX_TABLE
        routing_table_target = RegisterTargets.TARGET_NTT_ROUTING_TABLE
        if aux_table_name and routing_table_name:
            spad_map = QueueDict() # dict(var_name, (Variable, target_register))
            spad_map[aux_table_name]     = (self.mem_model.variables[aux_table_name],
                                            aux_table_target)
            spad_map[routing_table_name] = (self.mem_model.variables[routing_table_name],
                                            routing_table_target)
            # Load meta SPAD -> special CE rshuffle registers
            for shuffle_meta_table_name in spad_map:
                variable, target_idx = spad_map[shuffle_meta_table_name]
                assert variable.spad_address >= 0, f'Metadata variable {variable.name} must be in SPAD'
                self.queueCSyncmLoad(0, variable.spad_address)
                nload = cinst.NLoad(0, target_idx, variable, self.mem_model)
                nload.comment = f' loading routing table for `{rshuffle_data_type_name}`'
                nload.schedule(self.current_cycle, len(self.cinsts) + 1)
                self.cinsts.append(nload)
        else:
            raise RuntimeError(f'`rshuffle`: required routing table for `{rshuffle_data_type_name}` not present in metadata.')

    def loadBOnesMetadata(self,
                          spad_addr_offset: int,
                          ones_metadata_segment: int) -> int:
        """
        Queues MInstructions and CInstructions needed to load the Ones metadata.

        Parameters:
            spad_addr_offset (int): SPAD address offset where to store the metadata variables.
            ones_metadata_segment (int): Segment of Metadata Ones variables to load.
                                         The number of each segment is computed as
                                         `rns // constants.MemoryModel.MAX_RESIDUALS (64)`.
                                         Each segment contains the name of the variable containing identity metadata required
                                         to perform arithmetic computations for the corresponding set of residuals.

        Returns:
            int: Offset inside SPAD following the last location used to store the metadata variables.

        Raises:
            IndexError: If the requested segment index is out of range.
            RuntimeError: If the required number of twiddle metadata variables per segment is not met.
        """
        # Assert constants
        assert constants.MemoryModel.NUM_ONES_META_REGISTERS == 1

        if ones_metadata_segment < 0 or ones_metadata_segment >= len(self.mem_model.meta_ones_vars_segments):
            raise IndexError(('`twid_metadata_segment`: requested segment index {}, but there are only {} '
                              'segments of ones metadata available for up to {} residuals.').format(ones_metadata_segment,
                                                                                                    len(self.mem_model.meta_ones_vars_segments),
                                                                                                    len(self.mem_model.meta_ones_vars_segments) * constants.MemoryModel.MAX_RESIDUALS))

        RegisterTargets = constants.MemInfo.MetaTargets
        spad_addr = 0
        spad_map = QueueDict() # dict(var_name, (Variable, target_register))
        meta_ones_vars = self.mem_model.meta_ones_vars_segments[ones_metadata_segment]

        if meta_ones_vars \
            and len(meta_ones_vars) != constants.MemoryModel.NUM_ONES_META_REGISTERS:
            raise RuntimeError("Required {} twiddle metadata variables per segment, but {} received.".format(constants.MemoryModel.NUM_ONES_META_REGISTERS,
                                                                                                             len(meta_ones_vars)))

        # Load HBM -> SPAD
        for meta_ones_var_name in meta_ones_vars:
            target_spad_addr = spad_addr_offset + spad_addr
            # Clean up SPAD location (will cause undefined behavior if XInstQ is still executing)
            if self.mem_model.spad.buffer[target_spad_addr]:
                self.mem_model.spad.deallocate(target_spad_addr)
            # Load variable into SPAD
            variable = self.mem_model.variables[meta_ones_var_name]
            self.queueMLoad(0, target_spad_addr, variable,
                            comment='loading ones metadata for residuals [{}, {})'.format(ones_metadata_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                     (ones_metadata_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))
            spad_map[constants.MemInfo.MetaFields.FIELD_ONES] = (variable, RegisterTargets.TARGET_ONES)
            spad_addr += 1

        # Load meta SPAD -> special CE ones register
        for ones_meta_name in spad_map:
            variable, target_idx = spad_map[ones_meta_name]
            self.queueCSyncmLoad(0, variable.spad_address)
            bones = cinst.BOnes(0, target_idx, variable, self.mem_model,
                                comment='loading ones metadata for residuals [{}, {})'.format(ones_metadata_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                              (ones_metadata_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))
            bones.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(bones)

        # Update the currently loaded segment
        self.bundle_current_ones_segment = ones_metadata_segment

        return spad_addr_offset + spad_addr

    def loadTwiddleMetadata(self,
                            spad_addr_offset: int,
                            twid_metadata_segment: int):
        """
        Queues MInstructions and CInstructions needed to load the Twiddle factor generation metadata.

        Must not be called while XInstQ is executing.

        Parameters:
            spad_addr_offset (int): SPAD address offset where to store the metadata variables.
            twid_metadata_segment (int): Segment of Metadata Twiddle variables to load. Each segment is a list that
                                         contains self.mem_model.MAX_TWIDDLE_META_VARS_PER_SEGMENT (8) variable names.
                                         The number of each segment is computed as
                                         `rns // constants.MemoryModel.MAX_RESIDUALS (64)`.
                                         Each segment contains the name of the metadata variables required to compute
                                         the twiddle factors for the corresponding set of residuals.

        Returns:
            int: Offset inside SPAD following the last location used to store the metadata variables.

        Raises:
            IndexError: If the requested segment index is out of range.
            RuntimeError: If the required number of twiddle metadata variables per segment is not met.
        """
        spad_addr = 0

        if twid_metadata_segment < 0 or twid_metadata_segment >= len(self.mem_model.meta_twiddle_vars_segments):
            raise IndexError(('`twid_metadata_segment`: requested segment index {}, but there are only {} '
                              'segments of twiddle metadata available for up to {} residuals.').format(twid_metadata_segment,
                                                                                                       len(self.mem_model.meta_twiddle_vars_segments),
                                                                                                       len(self.mem_model.meta_twiddle_vars_segments) * constants.MemoryModel.MAX_RESIDUALS))

        meta_twiddle_vars = self.mem_model.meta_twiddle_vars_segments[twid_metadata_segment]

        if meta_twiddle_vars \
            and len(meta_twiddle_vars) != self.mem_model.MAX_TWIDDLE_META_VARS_PER_SEGMENT:
            raise RuntimeError("Required {} twiddle metadata variables per segment, but {} received.".format(self.mem_model.MAX_TWIDDLE_META_VARS_PER_SEGMENT,
                                                                                                             len(meta_twiddle_vars)))

        # Load HBM -> SPAD
        for meta_twiddle_var_name in meta_twiddle_vars:
            target_spad_addr = spad_addr_offset + spad_addr
            # Clean up SPAD location (will cause undefined behavior if XInstQ is still executing)
            if self.mem_model.spad.buffer[target_spad_addr]:
                self.mem_model.spad.deallocate(target_spad_addr)
            # Load variable into SPAD
            variable = self.mem_model.variables[meta_twiddle_var_name]
            self.queueMLoad(0, target_spad_addr, variable,
                            comment='loading twid metadata for residuals [{}, {})'.format(twid_metadata_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                     (twid_metadata_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))
            spad_addr += 1

        # Load meta SPAD -> special CE twiddle registers
        target_bload_register = 0
        for meta_twiddle_var_name in meta_twiddle_vars:
            variable = self.mem_model.variables[meta_twiddle_var_name]
            for col_num in range(constants.MemoryModel.NUM_BLOCKS_PER_TWID_META_WORD): # Block
                self.queueCSyncmLoad(0, variable.spad_address)
                bload = cinst.BLoad(0,
                                    col_num,
                                    target_bload_register,
                                    variable,
                                    self.mem_model,
                                    comment='loading twid metadata for residuals [{}, {})'.format(twid_metadata_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                                  (twid_metadata_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))
                bload.schedule(self.current_cycle, len(self.cinsts) + 1)
                self.cinsts.append(bload)
                target_bload_register += 1

        # Update the currently loaded segment
        self.bundle_current_twid_segment = twid_metadata_segment

        return spad_addr_offset + spad_addr

    def loadKeygenSeedMetadata(self,
                               spad_addr_offset: int,
                               kgseed_idx: int) -> int:
        """
        Queues MInstructions and CInstructions needed to load a new keygen seed.

        Keygen does not affect the XInstQ, and can be called to switch seeds when
        needed.

        Parameters:
            spad_addr_offset (int): SPAD address offset where to store the seed variable.
            kgseed_idx (int): Index of the seed to load. There are 4 seeds in a word. This index will
                              be properly mapped into (word, block) to load the proper seed.

        Returns:
            int: Offset inside SPAD following the last location used to store the metadata variable.

        Raises:
            IndexError: If the seed index is out of range.
        """
        if kgseed_idx < 0 \
           or kgseed_idx >= len(self.mem_model.meta_keygen_seed_vars) * constants.MemoryModel.NUM_BLOCKS_PER_KGSEED_META_WORD:
            raise IndexError('`kgseed_idx` must index in the range [0, {}), but {} received'.format(len(self.mem_model.meta_keygen_seed_vars) * constants.MemoryModel.NUM_BLOCKS_PER_KGSEED_META_WORD,
                                                                                                    kgseed_idx))
        # Only switch seeds if different from current
        if kgseed_idx != self.bundle_current_kgseed:

            spad_addr = 0
            # One word contains 4 seeds: find the right seed
            seed_word_block = kgseed_idx % constants.MemoryModel.NUM_BLOCKS_PER_KGSEED_META_WORD
            seed_word_idx = kgseed_idx // constants.MemoryModel.NUM_BLOCKS_PER_KGSEED_META_WORD
            seed_variable = None
            # Unfortunately, kg seeds are not contained in a list,
            # so we have to loop through the container to find the var name based on index
            for idx, var_name in enumerate(self.mem_model.meta_keygen_seed_vars):
                if idx == seed_word_idx:
                    seed_variable = self.mem_model.variables[var_name]
                    break

            # Load HBM -> SPAD
            target_spad_addr = spad_addr_offset + spad_addr
            # Clean up SPAD location (will cause undefined behavior if XInstQ is still executing)
            if self.mem_model.spad.buffer[target_spad_addr]:
                self.mem_model.spad.deallocate(target_spad_addr)
            # Load variable into SPAD
            self.queueMLoad(0, target_spad_addr, seed_variable,
                            comment='loading keygen seed ({}, block = {})'.format(seed_word_idx,
                                                                                  seed_word_block))
            spad_addr += 1

            # Load seed SPAD -> key material generation subsystem

            self.queueCSyncmLoad(len(self.cinsts), seed_variable.spad_address)

            kg_seed = cinst.KGSeed(len(self.cinsts),
                                   seed_word_block,
                                   seed_variable,
                                   self.mem_model)
            kg_start = cinst.KGStart(len(self.cinsts) + 1, comment=f'seed {kgseed_idx}')

            kg_seed.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(kg_seed)
            kg_start.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(kg_start)

            # Update the currently loaded seed
            self.bundle_current_kgseed = kgseed_idx
            self.last_keygen_index     = -1 # Restart the keygen index

        return spad_addr_offset + spad_addr

    def loadMetadata(self):
        """
        Loads initial metadata at the start of the program.
        """
        spad_addr_offset = 0
        spad_addr_offset = self.prepareShuffleMetadata(spad_addr_offset)
        self.metadata_spad_addr_start_twid = spad_addr_offset
        spad_addr_offset = self.loadTwiddleMetadata(spad_addr_offset, 0)
        self.metadata_spad_addr_start_ones = spad_addr_offset
        spad_addr_offset = self.loadBOnesMetadata(spad_addr_offset, 0)
        if len(self.mem_model.meta_keygen_seed_vars) > 0:
            # Keygen used in this program
            self.metadata_spad_addr_start_kgseed = spad_addr_offset
            spad_addr_offset = self.loadKeygenSeedMetadata(spad_addr_offset, 0)

    def prepareShuffleMetadata(self,
                               spad_addr_offset: int) -> int:
        """
        Queues MInstructions needed to load the `rshuffle` metadata into SPAD.

        Parameters:
            spad_addr_offset (int): SPAD address offset where to store the metadata variables.

        Returns:
            int: Offset inside SPAD following the last location used to store the metadata variables.

        Raises:
            RuntimeError: If both NTT Auxiliary table and Routing table or both iNTT Auxiliary table and Routing table do not exist in memory model.
        """
        spad_addr = 0

        # Load HBM -> SPAD
        if self.mem_model.meta_ntt_aux_table \
           and self.mem_model.meta_ntt_routing_table:
            variable = self.mem_model.variables[self.mem_model.meta_ntt_aux_table]
            self.queueMLoad(0, spad_addr_offset + spad_addr, variable)
            spad_addr += 1

            variable = self.mem_model.variables[self.mem_model.meta_ntt_routing_table]
            self.queueMLoad(0, spad_addr_offset + spad_addr, variable)
            spad_addr += 1
        else:
            # If one of NTT aux table or routing table is specified, so must be the other
            raise RuntimeError('Both, NTT Auxiliary table and Routing table must exist in memory model.')

        if self.mem_model.meta_intt_aux_table \
           and self.mem_model.meta_intt_routing_table:
            variable = self.mem_model.variables[self.mem_model.meta_intt_aux_table]
            self.queueMLoad(0, spad_addr_offset + spad_addr, variable)
            spad_addr += 1

            variable = self.mem_model.variables[self.mem_model.meta_intt_routing_table]
            self.queueMLoad(0, spad_addr_offset + spad_addr, variable)
            spad_addr += 1
        else:
            # If one of iNTT aux table or routing table is specified, so must be the other
            raise RuntimeError('Both, iNTT Auxiliary table and Routing table must exist in memory model.')

        return spad_addr_offset + spad_addr

    def priority_queue_push(self, xinstr, tie_breaker = None):
        """
        Adds a new instruction to the priority queue.

        Instructions added will be correctly handled by all priority queues.

        Parameters:
            xinstr: The instruction to add to the priority queue.
            tie_breaker (optional): The tie breaker value. Defaults to None.

        Raises:
            AssertionError: If the instruction is not in the dependency graph.
        """
        assert xinstr.id in self.dependency_graph, f'{xinstr.id} NOT in simulation.dependency_graph'
        if isinstance(xinstr, xinst.XStore):
            if tie_breaker is None:
                tie_breaker = (-1, )
                self.xstore_pq.push(xinstr.cycle_ready, xinstr, tie_breaker)
        if isinstance(xinstr, xinst.Move):
            if tie_breaker is None:
                tie_breaker = (-2, )
        self.priority_queue.push(xinstr.cycle_ready, xinstr, tie_breaker)
        self.set_extracted_xinstrs.add(xinstr.id)

    def priority_queue_remove(self, xinstr):
        """
        Removes an instruction from the priority queue.

        Instructions removed will be correctly handled by all priority queues.

        Parameters:
            xinstr: The instruction to remove from the priority queue.
        """
        self.priority_queue.remove(xinstr)
        if xinstr in self.xstore_pq:
            assert isinstance(xinstr, xinst.XStore)
            self.xstore_pq.remove(xinstr)

    def queueCSyncmLoad(self,
                        instr_id: int,
                        source_spad_addr: int):
        """
        Checks if needed, and, if so, queues a CSyncm CInstruction to sync to
        SPAD access from HBM in order to write from SPAD into CE.

        Parameters:
            instr_id (int): ID for the MSyncc instruction.
            source_spad_addr (int): SPAD address to sync to for writing.
        """
        last_mload_access = self.mem_model.spad.getAccessTracking(source_spad_addr).last_mload[1]
        if last_mload_access:
            # Need to sync to MInst
            csyncm = cinst.CSyncm(instr_id, last_mload_access)
            csyncm.schedule(self.current_cycle, len(self.cinsts) + 1)
            self.cinsts.append(csyncm)

    def queueMLoad(self,
                   instr_id: int,
                   target_spad_addr: int,
                   variable,
                   comment = ""):
        """
        Generates instructions to copy from HBM into SPAD.

        Parameters:
            instr_id (int): The ID of the instruction.
            target_spad_addr (int): The target SPAD address.
            variable: The variable to load.
            comment (optional): A comment associated with the instruction. Defaults to an empty string.

        Raises:
            ValueError: If the target SPAD address is negative.
            RuntimeError: If the variable is not found in HBM or if out of HBM space.
        """
        # Generate instructions to copy from HBM into SPAD
        if target_spad_addr < 0:
            raise ValueError('Argument Null Exception: Target SPAD address cannot be null (negative address).')

        self.queueMSynccLoad(instr_id, target_spad_addr)
        if variable.hbm_address < 0:
            if not auto_allocate:
                raise RuntimeError(f"Variable {variable.name} not found in HBM.")
            hbm_addr = self.mem_model.hbm.findAvailableAddress(self.mem_model.output_variables)
            if hbm_addr < 0:
                raise RuntimeError("Out of HBM space.")
            self.mem_model.hbm.allocateForce(hbm_addr, variable)
        mload = minst.MLoad(instr_id, [ variable ], self.mem_model, target_spad_addr, comment=comment)
        mload.schedule(self.current_cycle, len(self.minsts) + 1)
        self.minsts.append(mload)

    def queueMSynccLoad(self,
                        instr_id: int,
                        target_spad_addr: int):
        """
        Checks if needed, and, if so, queues an MSyncc MInstruction to sync to
        SPAD access to write from HBM into specified SPAD address.

        Parameters:
            instr_id (int): ID for the MSyncc instruction.
            target_spad_addr (int): SPAD address to sync to for writing.

        Raises:
            ValueError: If the target SPAD address is negative.
        """
        if target_spad_addr < 0:
            raise ValueError('Argument Null Exception: Target SPAD address cannot be null (negative address).')

        # mload depends on the last c access (cload or cstore)
        last_access = self.mem_model.spad.getAccessTracking(target_spad_addr)
        last_c_access = last_access.last_cstore
        if not last_access.last_cstore[1] \
            or (last_access.last_cload[1] \
                and last_access.last_cload[0] > last_access.last_cstore[0]):
            # No last cstore or cload happened after cstore
            last_c_access = last_access.last_cload
        last_c_access = last_c_access[1]
        if last_c_access:
            # Need to sync to CInst
            assert(last_c_access.is_scheduled)
            msyncc = minst.MSyncc(instr_id, last_c_access)
            msyncc.schedule(self.current_cycle, len(self.minsts) + 1)
            self.minsts.append(msyncc)

    def updateQueuesSyncsPass2(self):
        """
        Updates the msyncc and csyncm to correct instruction index
        after the scheduling completes.

        This is the second pass.
        """
        # Create reverse look-up maps for all CInsts and MInsts

        map_cinsts = dict((cinstr.id, idx) for idx, cinstr in enumerate(self.cinsts))
        map_minsts = dict((minstr.id, idx) for idx, minstr in enumerate(self.minsts))

        # Traverse MInstQ and update msyncc targets
        for minstr in self.minsts:
            if isinstance(minstr, minst.MSyncc):
                target_cinstr = minstr.cinstr
                if isinstance(target_cinstr, cinst.CExit):
                    # Rule, msyncc pointing to cexit, has to point to the next instruction
                    target_cinstr.set_schedule_timing_index(map_cinsts[target_cinstr.id] + 1)
                else:
                    target_cinstr.set_schedule_timing_index(map_cinsts[target_cinstr.id])
                minstr.freeze() # Re-freeze with new value

        # Traverse CInstQ and update csyncm targets
        for cinstr in self.cinsts:
            if isinstance(cinstr, cinst.CSyncm):
                target_minstr = cinstr.minstr
                target_minstr.set_schedule_timing_index(map_minsts[target_minstr.id])
                cinstr.freeze() # Re-freeze with new value

    def updateSchedule(self, instr) -> bool:
        """
        Updates the simulation pending schedule after `instr` has been scheduled.

        Parameters:
            instr: An instruction in the dependency graph.

        Returns:
            bool: True if bundle is full after scheduling the instruction, False otherwise.

        Raises:
            ValueError: If `instr` is None or not in the dependency graph.
            RuntimeError: If the bundle is already full or if an attempt is made to schedule an instruction in a bundle that only allows specific types or residuals.
        """
        if not instr:
            raise ValueError('`instr` cannot be `None`.')
        if instr.id not in self.dependency_graph:
            raise ValueError(f'`instr`: invalid instruction "{instr}" not in dependency graph.')
        if len(self.xinsts_bundle) >= self.max_bundle_size:
            raise RuntimeError("Bundle already full.")

        dependents = list(self.dependency_graph.successors(instr.id)) # Find instructions that depend on this instruction
        self.dependency_graph.remove_node(instr.id) # Remove from graph to update the in_degree of dependent instrs
        self.b_dependency_graph_changed = True
        # "move" dependent instrs that have no other dependencies to the top of the topo sort
        if isinstance(instr, xinst.XStore):
            for instr_id in dependents:
                if self.dependency_graph.in_degree(instr_id) <= 0:
                    if instr_id not in self.set_extracted_xinstrs:
                        self.priority_queue_push(self.dependency_graph.nodes[instr_id]['instruction'])
        else:
            self.topo_sort = [ instr_id for instr_id in dependents if self.dependency_graph.in_degree(instr_id) <= 0 ] + self.topo_sort
            self.b_topo_sort_changed = True

        if instr in self.priority_queue:
            self.priority_queue_remove(instr)

        # Do not search the topo sort to actually remove the duplicated instrs because it is O(N) costly:
        # set_extracted_xinstrs will take care of skipping them once encountered.

        self.scheduled_xinsts_count += 1

        if isinstance(instr, xinst.XStore):
            # Add corresponding cstore
            cstore = cinst.CStore(instr.id[0],
                                  self.mem_model,
                                  comment=instr.comment)
            self.post_bundle_cinsts.append(cstore)
            # Make sure bundle syncs to last mstore before fetching because
            # it does cstores that overwrite SPAD addresses that may still be in process
            # of storing to HBM:
            last_mstore = self.mem_model.spad.getAccessTracking(instr.dest_spad_address).last_mstore
            if self.pre_bundle_csync_minstr[0] <= last_mstore[0] \
               and last_mstore[1] is not None:
                self.pre_bundle_csync_minstr = last_mstore

        if isinstance(instr, (xinst.rShuffle, xinst.irShuffle)):
            # Rule: no more than one write to same bank in the same cycle.
            # rshuffles have different latency than other XInsts, so, we must ensure that their
            # write cycle is respected.

            # Add rshuffle to list of pending writes
            scheduled_cycle = instr.schedule_timing.cycle
            write_cycle = XWriteCycleTrack(cycle = CycleType(bundle = scheduled_cycle.bundle,
                                                             cycle = scheduled_cycle.cycle + instr.latency - 1),
                                           banks = set(v.suggested_bank for v in instr.dests))
            self.pending_write_cycles.append(write_cycle)

            # Track the scheduled xrshuffle to try to schedule others in slotted intervals
            self.last_xrshuffle = instr

            # Rule: cannot mix rShuffle and irShuffle in same bundle.

            if self.bundle_needed_rshuffle_type is None:
                self.bundle_needed_rshuffle_type = type(instr)
            elif not isinstance(instr, self.bundle_needed_rshuffle_type):
                raise RuntimeError('Attempted to schedule {} in bundle that only allows {}.'.format(instr,
                                                                                                    self.bundle_needed_rshuffle_type))

        # Rule: cannot mix XInsts of different residual segments in same bundle.
        if instr.res is not None:
            instr_needed_segment = instr.res // constants.MemoryModel.MAX_RESIDUALS
            assert self.bundle_needed_ones_segment == self.bundle_needed_twid_segment, \
                'Needed Ones and Twiddle metadata segments are not synchronized.'
            if self.bundle_needed_ones_segment == -1:
                self.bundle_needed_ones_segment = instr_needed_segment
            elif self.bundle_needed_ones_segment != instr_needed_segment:
                raise RuntimeError(('Attempted to schedule XInstruction "{}", residual = {}, '
                                    'in bundle {} that only allows residuals in range [{}, {}).').format(str(instr),
                                                                                                         instr.res,
                                                                                                         self.current_cycle.bundle,
                                                                                                         self.bundle_needed_ones_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                                         (self.bundle_needed_ones_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))
            if self.bundle_needed_twid_segment == -1:
                self.bundle_needed_twid_segment = instr_needed_segment
            elif self.bundle_needed_twid_segment != instr_needed_segment:
                raise RuntimeError(('Attempted to schedule XInstruction {}, residual = {}, '
                                    'in bundle {} that only allows residuals in range [{}, {}).').format(str(instr),
                                                                                                         instr.res,
                                                                                                         self.current_cycle.bundle,
                                                                                                         self.bundle_needed_twid_segment * constants.MemoryModel.MAX_RESIDUALS,
                                                                                                         (self.bundle_needed_twid_segment + 1) * constants.MemoryModel.MAX_RESIDUALS))

        self.appendXInstToBundle(instr) # add instruction to bundle

        # True <=> bundle needs to be flushed (because of exit or full)
        return isinstance(instr, xinst.Exit) \
            or (len(self.xinsts_bundle) >= self.max_bundle_size)

def __canScheduleInBundle(instr, simulation: Simulation, padding: int = 1) -> bool:
    """
    Determines if an instruction can be scheduled in the current bundle.

    Parameters:
        instr: The instruction to be scheduled.
        simulation (Simulation): The current simulation context.
        padding (int): Extra instruction padding (like number of other instructions before this one, such as a nop).

    Returns:
        bool: True if the instruction can be scheduled in the current bundle, False otherwise.
    """
    # TODO:
    # Look into this function to see if we can bring back skip scheduling of rshuffles at the end of bundles.
    # Right now, this featuer is disabled because ifetch does not have the same latency as XInstrs, so
    # the simulation keeps track of the whole bundle latency and just adds nops to the CInstQ as needed.
    #-----------------
    return len(simulation.xinsts_bundle) < simulation.max_bundle_size and True

def __flushVariableFromSPAD(instr, dest_hbm_addr: int, variable: Variable, simulation: Simulation) -> bool:
    """
    Flushes a variable from the SPAD to HBM.

    Parameters:
        instr: The instruction triggering the flush.
        dest_hbm_addr (int): The destination address in HBM.
        variable (Variable): The variable to be flushed.
        simulation (Simulation): The current simulation context.

    Returns:
        bool: True if the flush was scheduled successfully, False otherwise.

    Raises:
        AssertionError: If the destination HBM address is invalid.
    """
    assert(dest_hbm_addr >= 0)

    spad = simulation.mem_model.spad

    comment = (' id: {} - flushing').format(instr.id)
    last_cstore = spad.getAccessTracking(variable.spad_address).last_cstore[1]
    if last_cstore:
        # mstore needs to happen after last cstore
        assert(last_cstore.is_scheduled)
        # Sync to last CInst access to avoid storing before access completes
        msyncc = minst.MSyncc(instr.id[0], last_cstore, comment=comment)
        msyncc.schedule(simulation.current_cycle, len(simulation.minsts) + 1)
        simulation.minsts.append(msyncc)

    mstore = minst.MStore(instr.id[0], [variable], simulation.mem_model, dest_hbm_addr, comment=comment)
    mstore.schedule(simulation.current_cycle, len(simulation.minsts) + 1)
    simulation.minsts.append(mstore)

    return True

def _createXStore(instr_id: int, dest_spad_addr: int, evict_variable: Variable, new_variable: Variable, comment: str, simulation: Simulation) -> object:
    """
    Creates an XStore instruction to move a variable into SPAD.

    Parameters:
        instr_id (int): The instruction ID.
        dest_spad_addr (int): The destination SPAD address.
        evict_variable (Variable): The variable to evict.
        new_variable (Variable): The variable to be allocated in register after eviction, or None to keep register free.
        comment (str): A comment for the instruction.
        simulation (Simulation): The current simulation context.

    Returns:
        object: The created XStore instruction.

    Raises:
        AssertionError: If the evict variable's register is None or if the SPAD address is invalid.
    """
    assert(evict_variable.register is not None)
    assert(evict_variable.spad_address < 0 or evict_variable.spad_address == dest_spad_addr)

    spad = simulation.mem_model.spad

    # Block SPAD address to avoid it being found by another findSPADAddress
    if spad[dest_spad_addr]:
        assert(not isinstance(spad[dest_spad_addr], DummyVariable))
        spad.deallocate(dest_spad_addr)
    spad.allocateForce(dest_spad_addr, DummyVariable())
    # Generate the xstore instruction to move variable into SPAD
    xstore = XStoreAssign(instr_id, [evict_variable], simulation.mem_model, new_variable, dest_spad_addr=dest_spad_addr, comment=comment) \
        if new_variable else \
        xinst.XStore(instr_id, [evict_variable], simulation.mem_model, dest_spad_addr=dest_spad_addr, comment=comment)
    evict_variable.accessed_by_xinsts = [Variable.AccessElement(0, xstore.id)] + evict_variable.accessed_by_xinsts

    return xstore

def __flushVariableFromRegisterFile(instr, dest_spad_addr: int, evict_variable: Variable, new_variable: Variable, simulation: Simulation) -> object:
    """
    Flushes a variable from the register file to SPAD.

    Parameters:
        instr: The instruction triggering the flush.
        dest_spad_addr (int): The destination SPAD address.
        evict_variable (Variable): The variable to evict.
        new_variable (Variable): The variable to be allocated in register after eviction, or None to keep register free.
        simulation (Simulation): The current simulation context.

    Returns:
        object: The created XStore instruction.
    """
    comment = (' dep id: {} - flushing'.format(instr.id))
    xstore = _createXStore(instr.id[0], dest_spad_addr, evict_variable, new_variable, comment, simulation)
    simulation.addDependency(xstore, instr)

    return xstore

def scheduleXNOP(instr, idle_cycles: int, simulation: Simulation, force_nop: bool = False) -> bool:
    """
    Schedules a NOP instruction if necessary.

    Parameters:
        instr: The instruction that requires the NOP.
        idle_cycles (int): The number of idle cycles to schedule.
        simulation (Simulation): The current simulation context.
        force_nop (bool): Whether to force the scheduling of a NOP.

    Returns:
        bool: True if the NOP was scheduled, False otherwise.

    Raises:
        ValueError: If idle_cycles is not greater than 0.
    """
    if idle_cycles <= 0:
        raise ValueError(f'`idle_cycles`: expected greater than `0`, but {idle_cycles} received.')

    retval = True

    comment = ""
    if not isinstance(instr, xinst.Exit):
        comment = f" nop for not ready instr {instr.id}"
    #prev_xinst = simulation.xinsts_bundle[-1] if len(simulation.xinsts_bundle) > 0 else None
    prev_xinst = None # rshuffle wait cycle no longer works
    if not force_nop and isinstance(prev_xinst, (xinst.rShuffle, xinst.irShuffle)):
        # Add idle cycles using previous rshuffle
        prev_xinst.wait_cyc = idle_cycles
        if comment:
            prev_xinst.comment += "{} {}".format(";" if len(prev_xinst.comment) > 0 else "", comment)
        prev_xinst.freeze()  # Refreeze rshuffle to reflect the new wait_cyc
        simulation.current_cycle += idle_cycles # Advance current cycle
    else:
        retval = force_nop or len(simulation.xinsts_bundle) < simulation.max_bundle_size - 1
        if retval:
            assert len(simulation.xinsts_bundle) < simulation.max_bundle_size, 'Cannot queue NOP into full bundle.'
            xnop = xinst.Nop(instr.id[0], idle_cycles, comment=comment)
            simulation.current_cycle += xnop.schedule(simulation.current_cycle, len(simulation.xinsts_bundle) + 1)
            simulation.appendXInstToBundle(xnop)

    return retval

def findSPADAddress(instr, simulation: Simulation) -> int:
    """
    Finds an available SPAD address for an instruction.

    Parameters:
        instr: The instruction needing SPAD.
        simulation (Simulation): The current simulation context.

    Returns:
        int: The SPAD address, or -1 if no address is available.

    Raises:
        RuntimeError: If no SPAD address is available or if HBM is full.
    """
    # Logic:
    #   if found empty spad_address:
    #       return spad_address
    #   else if no empty spad_address:
    #       Eviction (removal) of variable from SPAD needed
    #       find spad_address to evict using replacement policy and avoid live variables
    #       if found spad_address to evict:
    #           Eviction:
    #               if variable to evict is in register:
    #                   no need to flush SPAD, just evict variable since it is in active use in register file (mark as dirty in register).
    #               else if variable is dirty in spad:
    #                   flush (copy) variable to HBM, and evict from SPAD
    #           return spad_address
    #   if no spad_address found:
    #       return null spad_address (-1)
    #
    # returns retval_addr: int
    # retval_addr < 0 if no address is available in SPAD for this bundle

    # Find an address in SPAD
    spad = simulation.mem_model.spad
    # Make live_vars be all variables in SPAD not in registers
    live_vars = set(var_name for var_name in simulation.live_vars if var_name in spad and spad[var_name].register is None)
    retval_addr: int = spad.findAvailableAddress(live_vars, simulation.replacement_policy)
    if retval_addr < 0:
        # Drastic measure to avoid running our of SPAD
        # retval_addr: int = spad.findAvailableAddress(set(), simulation.replacement_policy)

        # Not implemented: throws if spad is full of live variables
        raise RuntimeError(f"No SPAD address available. Bundle {simulation.current_cycle.bundle}")
    if retval_addr >= 0:
        # SPAD address found
        variable: Variable = spad.buffer[retval_addr]
        if variable:  # Contains a variable
            assert(variable.spad_address == retval_addr)
            # Address needs to be evicted
            if variable.spad_dirty:
                # Check usage
                if len(variable.accessed_by_xinsts) > 0 or variable.name in simulation.mem_model.output_variables:
                    # Check if SPAD flush is necessary
                    if not variable.register:
                        # SPAD flush necessary

                        if variable.hbm_address < 0:
                            # Need a new location in HBM to store the variable
                            new_hbm_addr = simulation.mem_model.hbm.findAvailableAddress(simulation.mem_model.output_variables)
                        else:
                            # Variable already has a location in SPAD
                            new_hbm_addr = variable.hbm_address

                        if new_hbm_addr < 0:
                            # HBM full
                            raise RuntimeError("Out of HBM space.")

                        # Found HBM address

                        # Queue operations to flush SPAD
                        # (this will deallocate variable from SPAD)
                        evict_scheduled = __flushVariableFromSPAD(instr, new_hbm_addr, variable, simulation)
                        if not evict_scheduled:
                            retval_addr = -1  # Could not schedule the eviction in this cycle

                    else:  # Variable resides in register
                        # Mark register as dirty to make sure we flush to cache when done in the register file
                        variable.register_dirty = True
                        # Now, just clear cache and keep it in register
                else:
                    # Variable no longer used by remaining XInstructions,
                    # so, just get rid of it
                    variable.spad_dirty = False

            if retval_addr >= 0:
                if variable.spad_address >= 0:
                    assert(variable.spad_address == retval_addr)
                    # Variable still in SPAD
                    # SPAD address now clean, just free the address
                    spad.deallocate(retval_addr)

    return retval_addr

def findRegister(instr, bank_idx: int, simulation: Simulation, override_replacement_policy: str = None, dest_var: Variable = None) -> object:
    """
    Finds an available register for an instruction.

    Parameters:
        instr: The instruction needing a register.
        bank_idx (int): The index of the register bank.
        simulation (Simulation): The current simulation context.
        override_replacement_policy (str): The replacement policy to override, if any.
        dest_var (Variable): The variable to be allocated in register after eviction, or None to keep register free.

    Returns:
        tuple: A tuple containing the ready value (int) and the register or XInstruction.

    Raises:
        RuntimeError: If no SPAD address is available or if HBM is full.
    """
    # Logic:
    #   find empty retval_register in register file
    #   if retval_register found:
    #       return retval_register
    #   else if no empty register:
    #       Eviction (removal) of variable from register file needed
    #       find retval_register to evict using replacement policy and avoid live variables
    #       if found retval_register to evict:
    #           Eviction:
    #               if register is clean:
    #                   no need to flush register, just evict variable since it has not been writen to.
    #               else, register is dirty:
    #                   need to flush variable to SPAD cache:
    #                   flush logic:
    #                       find appropriate SPAD address to flush to.
    #                       if no SPAD address found:
    #                           return null retval_register (None)
    #                       else, SPAD address found:
    #                           copy variable from register to SPAD
    #                   evict variable from register
    #           return retval_register
    #   if no retval_register found:
    #       return null retval_register (None)
    #
    # returns ready_value: int, retval_register: Register if ready_value == 1 else XInstruction
    # retval_register is None if no register is available for this bundle

    def inner_computeLiveVars(register_bank):
        # Returns an iterable over all variable names in the register bank that are live variables
        for r_i in range(register_bank.register_count):
            v: Variable = register_bank.getRegister(r_i).contained_variable
            if v and v.name and ((v.name in simulation.live_vars) or (v.cycle_ready > simulation.current_cycle)):
                yield v.name

    retval = 1
    if override_replacement_policy is None:
        override_replacement_policy = simulation.replacement_policy

    # Find a register from specified bank
    register_bank = simulation.mem_model.register_banks[bank_idx]
    # Compute live variables
    live_vars = set(inner_computeLiveVars(register_bank))

    retval_register: Register = register_bank.findAvailableRegister(live_vars, override_replacement_policy)
    if retval_register:
        # Register found
        if retval_register.contained_variable:
            # Register needs to evict contained variable
            variable = retval_register.contained_variable
            assert(not isinstance(variable, DummyVariable))
            if variable.register_dirty:
                # Check usage
                if len(variable.accessed_by_xinsts) > 0 or variable.name in simulation.mem_model.output_variables:
                    # Flush necessary
                    if variable.spad_address < 0:
                        # Need a new location in SPAD to store the variable
                        new_spad_addr = findSPADAddress(instr, simulation)
                    else:
                        # Variable already has a location in SPAD
                        new_spad_addr = variable.spad_address

                    if new_spad_addr < 0:
                        # No SPAD address available this bundle
                        retval_register = None
                        retval = 0
                    else:
                        # Found SPAD address

                        # Evict variable
                        retval_register = __flushVariableFromRegisterFile(instr, new_spad_addr, variable, dest_var, simulation)
                        retval = 2
                else:
                    # Variable no longer used by remaining XInstructions,
                    # so, just get rid of it
                    variable.register_dirty = False

        if retval == 1:  # Register clean
            # No eviction is necessary, just free the register for destination variable (or none if no destination)
            retval_register.allocateVariable(dest_var)

    if not retval_register:
        retval = 0

    return retval, retval_register

def loadVariableHBMToSPAD(instr, variable: Variable, simulation: Simulation) -> bool:
    """
    Loads a variable from HBM to SPAD.

    Parameters:
        instr: The instruction needing the variable.
        variable (Variable): The variable to be loaded.
        simulation (Simulation): The current simulation context.

    Returns:
        bool: True if the variable was loaded successfully, False otherwise.

    Raises:
        RuntimeError: If the variable is not found in HBM or if HBM is full.
    """
    # Schedules a list of instructions needed to load the specified variable from HBM into SPAD.
    spad = simulation.mem_model.spad

    target_spad_addr = -1  # This will be used as our flag to track valid state (-1 = not valid)

    if variable.name not in simulation.mem_model.store_buffer:  # Check variable is not in transit from CE
        if variable.spad_address >= 0:
            # Variable already in SPAD
            target_spad_addr = variable.spad_address
        else:
            # Bring variable from HBM into SPAD

            # Need a new location in SPAD to store the variable
            target_spad_addr = findSPADAddress(instr, simulation)
            if target_spad_addr >= 0:
                # We are still in valid state

                # Generate instructions to copy from HBM into SPAD

                # Mload depends on the last c access (cload or cstore)
                last_access = spad.getAccessTracking(target_spad_addr)
                last_c_access = last_access.last_cstore
                if not last_access.last_cstore[1] or (last_access.last_cload[1] and last_access.last_cload[0] > last_access.last_cstore[0]):
                    # No last cstore or cload happened after cstore
                    last_c_access = last_access.last_cload
                last_c_access = last_c_access[1]
                if last_c_access:
                    # Need to sync to CInst
                    assert(last_c_access.is_scheduled)
                    msyncc = minst.MSyncc(instr.id[0], last_c_access)
                    msyncc.schedule(simulation.current_cycle, len(simulation.minsts))
                    simulation.minsts.append(msyncc)
                if variable.hbm_address < 0:
                    hbm_addr = simulation.mem_model.hbm.findAvailableAddress(simulation.mem_model.output_variables)
                    if hbm_addr < 0:
                        raise RuntimeError("Out of HBM space.")
                    simulation.mem_model.hbm.allocateForce(hbm_addr, variable)
                mload = minst.MLoad(instr.id[0], [variable], simulation.mem_model, target_spad_addr, comment="dep id: {}".format(instr.id))
                mload.schedule(simulation.current_cycle, len(simulation.minsts) + 1)
                simulation.minsts.append(mload)

    return target_spad_addr >= 0

def hasBankWriteConflictGeneral(ready_cycle: CycleType, latency: int, banks, simulation: Simulation) -> bool:
    """
    Checks for bank write conflicts in general.

    Parameters:
        ready_cycle (CycleType): The cycle when the instruction is ready.
        latency (int): The latency of the instruction.
        banks: An iterable of bank indices.
        simulation (Simulation): The current simulation context.

    Returns:
        bool: True if there is a bank write conflict, False otherwise.
    """
    retval = False
    if ready_cycle.bundle <= simulation.current_cycle.bundle:  # Instruction has no conflicts if it is on a later bundle
        instr_write_cycle = XWriteCycleTrack(cycle=CycleType(bundle=simulation.current_cycle.bundle, cycle=max(ready_cycle.cycle, simulation.current_cycle.cycle) + latency - 1), banks=set(banks))
        if len(instr_write_cycle.banks) > 0:
            for rshuffle_write_cycle in simulation.pending_write_cycles:
                if instr_write_cycle.cycle < rshuffle_write_cycle.cycle:
                    # Instruction write cycle happens before conflicting with examined write cycle
                    # and thus will not conflict with any other write cycles in the list because it
                    # is ordered by write cycle
                    break
                # Check if we conflict
                if instr_write_cycle.cycle == rshuffle_write_cycle.cycle and len(instr_write_cycle.banks & rshuffle_write_cycle.banks) > 0:
                    # Instruction bank writes conflict with a previous write cycle
                    retval = True
                    break

    return retval

def hasBankWriteConflict(instr, simulation: Simulation) -> bool:
    """
    Checks for bank write conflicts for a specific instruction.

    Parameters:
        instr: The instruction to check.
        simulation (Simulation): The current simulation context.

    Returns:
        bool: True if there is a bank write conflict, False otherwise.
    """
    ready_cycle = instr.cycle_ready
    if ready_cycle.bundle < simulation.current_cycle.bundle:
        ready_cycle = CycleType(bundle=simulation.current_cycle.bundle, cycle=0)

    if isinstance(instr, xinst.XStore):
        banks = set()  # Xstore does not write to register file
    else:
        banks = set(v.suggested_bank for v in instr.dests if isinstance(v, Variable))
        banks |= set(r.bank.bank_index for r in instr.dests if isinstance(r, Register))

    return hasBankWriteConflictGeneral(ready_cycle, instr.latency, banks, simulation)

def prepareInstruction(original_xinstr, simulation: Simulation) -> int:
    """
    Prepares an instruction for scheduling.

    Parameters:
        original_xinstr: The original instruction to prepare.
        simulation (Simulation): The current simulation context.

    Returns:
        tuple: A tuple containing the ready value (int) and the instruction or None.

    Raises:
        RuntimeError: If a variable is not in the suggested bank.
    """
    # Schedules the specified instruction into the current bundle of xinsts.
    retval = 1  # Tracks whether we are valid for scheduling in current bundle
    retval_instr = original_xinstr

    # Check sources
    expanded_dests = original_xinstr.dests[:]  # Create a copy
    if retval == 1:
        for idx, src_var in enumerate(original_xinstr.sources):
            if idx == 2 and isinstance(original_xinstr, (xinst.NTT, xinst.iNTT)):
                # Special case for xntt: twiddles for stage 0 are ignored
                if original_xinstr.stage == 0:
                    expanded_dests.append(src_var)
                    continue  # Next source, but this should end the for-loop

            if retval != 1:
                break

            b_generated_keygen_var = False  # Flag to track whether this source variable is a generated keygen this time
            # Make sure destination variables are on a register
            if isinstance(src_var, Variable):
                if src_var.name in simulation.live_outs:
                    # Stop preparing and move instruction to next bundle: one of its variables is marked for eviction
                    retval = 0
                else:
                    simulation.addLiveVar(src_var.name, original_xinstr)  # Add variable as live
                    if not src_var.register:
                        # Needs to start at bank 0

                        b_generated_keygen_var = not simulation.mem_model.isVarInMem(src_var.name) and src_var.name in simulation.mem_model.keygen_variables

                        if not b_generated_keygen_var:
                            # Variable is not keygen or it has already been generated

                            # Load into SPAD
                            if src_var.spad_address < 0:
                                assert src_var.name not in simulation.mem_model.store_buffer, f'Attempting to load from HBM: "{src_var.name}"; already in transit in SPAD store buffer.'
                                if not loadVariableHBMToSPAD(original_xinstr, src_var, simulation):
                                    # Could not find location in SPAD, move to next bundle
                                    retval = 0

                        if retval != 0:
                            retval, new_instr_or_reg = findRegister(original_xinstr, 0, simulation, override_replacement_policy="")  # No replacement policy for bank 0
                            # retval == 1 => register good to go
                            # retval == 2 => xstore needed for eviction
                            if retval == 1:
                                # Register ready, load from SPAD
                                assert(new_instr_or_reg.bank.bank_index == 0)

                                if b_generated_keygen_var:
                                    # This is a keygen variable that has not been generated
                                    keygen_retval = simulation.generateKeyMaterial(original_xinstr.id[0], src_var, new_instr_or_reg)
                                    if keygen_retval == 2:
                                        # Could not generate key material this bundle
                                        retval = 3
                                else:
                                    # Generate instructions to load variable from SPAD into bank 0
                                    last_mload_access = simulation.mem_model.spad.getAccessTracking(src_var.spad_address).last_mload[1]
                                    if last_mload_access:
                                        # Need to sync to MInst
                                        csyncm = cinst.CSyncm(original_xinstr.id[0], last_mload_access)
                                        csyncm.schedule(simulation.current_cycle, len(simulation.cinsts) + 1)
                                        simulation.cinsts.append(csyncm)
                                    cload = cinst.CLoad(original_xinstr.id[0], new_instr_or_reg, [src_var], simulation.mem_model, comment="dep id: {}".format(original_xinstr.id))
                                    cload.schedule(simulation.current_cycle, len(simulation.cinsts) + 1)
                                    simulation.cinsts.append(cload)
                            if retval == 2:
                                # Register needs eviction
                                assert isinstance(new_instr_or_reg, xinst.XStore)
                                retval_instr = new_instr_or_reg
                            elif retval == 3:
                                # Could not generate key material this bundle
                                assert b_generated_keygen_var, f"Variable {src_var.name} is not keygen"
                                retval = 2

                    if retval == 1:
                        if src_var.register.bank.bank_index == 0:
                            # Already in bank 0, so, bring to correct bank
                            retval, new_instr_or_reg = findRegister(original_xinstr, src_var.suggested_bank, simulation)
                            # retval == 1 => register good to go
                            # retval == 2 => xstore needed for eviction
                            if retval == 1:
                                # Generate instruction to move variable from bank 0 to its suggested bank
                                new_instr_or_reg.allocateVariable(simulation.bundle_dummy_var)
                                xmove = xinst.Move(original_xinstr.id[0], new_instr_or_reg, [src_var], dummy_var=simulation.bundle_dummy_var)
                                if xmove.cycle_ready.bundle < simulation.current_cycle.bundle:
                                    # Correct cycle ready's bundle
                                    xmove.cycle_ready = CycleType(bundle=simulation.current_cycle.bundle, cycle=0)
                                if hasBankWriteConflict(xmove, simulation):
                                    xmove.cycle_ready = CycleType(bundle=xmove.cycle_ready.bundle, cycle=xmove.cycle_ready.cycle + 1)
                                    if not scheduleXNOP(xmove, 1, simulation):
                                        retval = 0
                                if retval != 0:
                                    src_var.accessed_by_xinsts = [Variable.AccessElement(0, xmove.id)] + src_var.accessed_by_xinsts
                                    simulation.addDependency(xmove, original_xinstr)
                                    new_instr_or_reg = xmove
                                    retval = 2  # Need xmove

                            if retval == 2:
                                # XInsts needed to prepare variable

                                # Moves should always be able to schedule at this point
                                assert isinstance(new_instr_or_reg, (xinst.Move, xinst.XStore))
                                retval_instr = new_instr_or_reg

                    if retval == 1:
                        if src_var.register.bank.bank_index != src_var.suggested_bank:
                            raise RuntimeError('Variable `{}` is in register `{}`, which is not in suggested bank {}.'.format(src_var.name, src_var.register.name, src_var.suggested_bank))
                        if b_generated_keygen_var:
                            # Mark register as dirty since this variable is keygen and
                            # does not exist elsewhere: we want to preserve this value
                            src_var.register_dirty = True

    # Check destinations
    if retval == 1:
        # Expanded_dests is original_xinstr.dests + any extra variables that need to be here
        for dst_var in expanded_dests:
            if retval != 1:
                break
            # Make sure destination variables are on a register
            if isinstance(dst_var, Variable):
                if dst_var.name in simulation.live_outs:
                    # Stop preparing and move instruction to next bundle: one of its variables is marked for eviction
                    retval = 0
                else:
                    simulation.addLiveVar(dst_var.name, original_xinstr)  # Add variable as live
                    if not dst_var.register:
                        # Find register for variable:
                        # This will schedule all the C and M instructions needed to secure that register
                        retval, new_instr_or_reg = findRegister(original_xinstr, dst_var.suggested_bank, simulation, dest_var=dst_var)

                        # retval == 1 => register good to go
                        # retval == 2 => xstore needed for eviction
                        if retval == 2:
                            assert isinstance(new_instr_or_reg, xinst.XStore)
                            retval_instr = new_instr_or_reg

                    if retval == 1:
                        if dst_var.register.bank.bank_index != dst_var.suggested_bank:
                            raise RuntimeError('Variable `{}` is in register `{}`, which is not in suggested bank {}.'.format(dst_var.name, dst_var.register.name, dst_var.suggested_bank))

    assert retval == 0 or (retval_instr is not None and __canScheduleInBundle(retval_instr, simulation))  # We should always be able to schedule preparation instructions

    if retval == 0:
        retval_instr = None
    elif retval_instr:
        assert retval_instr.id in simulation.dependency_graph
        if hasBankWriteConflict(retval_instr, simulation):
            assert not isinstance(retval_instr, xinst.Move)  # Moves must be scheduled immediately
            # Write cycle conflict found, so, update found instruction cycle ready
            new_cycle_ready = CycleType(bundle=simulation.current_cycle.bundle, cycle=max(retval_instr.cycle_ready.cycle, simulation.current_cycle.cycle) + 1)
            retval_instr.cycle_ready = new_cycle_ready

    return retval, retval_instr

def scheduleASMISAInstructions(dependency_graph: nx.DiGraph,
                               max_bundle_size: int,
                               mem_model: MemoryModel,
                               replacement_policy,
                               progress_verbose: bool = False) -> (list, list, list, int):
    """
    Schedules ASM-ISA instructions based on a dependency graph of XInsts to minimize idle cycles.

    Parameters:
        dependency_graph (nx.DiGraph): The dependency directed acyclic graph of XInsts.
        max_bundle_size (int): Maximum number of instructions in a bundle.
        mem_model (MemoryModel): The memory model used in the simulation.
        replacement_policy: The policy used for memory replacement.
        progress_verbose (bool): Whether to print progress information.

    Returns:
        tuple: A tuple containing lists of xinst, cinst, minst, and the total idle cycles.
    """
    simulation = Simulation(dependency_graph,
                            max_bundle_size, # Max number of instructions in a bundle
                            mem_model,
                            replacement_policy,
                            progress_verbose)
    # DEBUG
    iter_counter = 0
    pisa_instr_counter = 0
    # ENDDEBUG

    if progress_verbose:
        print('Dependency Graph')
        print(f'  Initial number of dependencies: {simulation.dependency_graph.size()}')
        print('Scheduling metadata preparation.')

    simulation.loadMetadata()

    if progress_verbose:
        print('Scheduling XInstructions...')

    try:
        b_flush_bundle = False
        fixed_last_short_bundle = -1  # Tracks last bundle considered short that got fixed
        new_bundle = True
        while simulation.dependency_graph:  # Iterates per instruction to be scheduled
            # DEBUG
            iter_counter += 1
            if GlobalConfig.debugVerbose:
                if iter_counter % int(GlobalConfig.debugVerbose) == 0:
                    print(iter_counter)
            # ENDDEBUG

            # Check if current bundle needs to be flushed
            if b_flush_bundle:
                simulation.flushBundle()
                b_flush_bundle = False  # Bundle flushed
                new_bundle = True

            # Check if we need to fetch more bundles
            if new_bundle and len(simulation.xinsts) % simulation.max_bundles_per_xinstfetch == 0:
                if progress_verbose:
                    pct = int(simulation.scheduled_xinsts_count * 100 / simulation.total_instructions)
                    print("{}% - {}/{}".format(pct,
                                               simulation.scheduled_xinsts_count,
                                               simulation.total_instructions))
                # Handle xinstfetch
                xinstfetch = cinst.XInstFetch(len(simulation.xinstfetch_cinsts_buffer),
                                              simulation.xinstfetch_xq_addr,
                                              simulation.xinstfetch_hbm_addr)
                xinstfetch.schedule(simulation.current_cycle, len(simulation.xinstfetch_cinsts_buffer) + 1)
                simulation.xinstfetch_cinsts_buffer.append(xinstfetch)

                simulation.xinstfetch_xq_addr = (simulation.xinstfetch_xq_addr + 1) % constants.MemoryModel.XINST_QUEUE_MAX_CAPACITY_WORDS
                simulation.xinstfetch_hbm_addr += 1
                # Check if we reached end of XInst queue
                if simulation.xinstfetch_xq_addr <= 0:
                    if GlobalConfig.useXInstFetch:
                        if progress_verbose:
                            print("XInst queue filled: wrapping around...")
                        # Flush buffered xinstfetches to cinst
                        simulation.cinsts = simulation.cinsts[:simulation.xinstfetch_location_idx_in_cinsts] \
                                            + simulation.xinstfetch_cinsts_buffer \
                                            + simulation.cinsts[simulation.xinstfetch_location_idx_in_cinsts:]
                    # Point to next location to insert xinstfetches
                    simulation.xinstfetch_location_idx_in_cinsts = len(simulation.cinsts)
                    simulation.xinstfetch_cinsts_buffer = []  # Buffer flushed, start new

            new_bundle = False

            # Remove any write cycles that have passed
            simulation.cleanupPendingWriteCycles()

            while True: # do/while
                if simulation.topo_start_idx < len(simulation.full_topo_sort) \
                   and len(simulation.topo_sort) < Simulation.MIN_INSTRUCTIONS_IN_TOPO_SORT:
                    if len(simulation.priority_queue) < Simulation.MIN_INSTRUCTIONS_IN_TOPO_SORT:
                        simulation.topo_sort += simulation.full_topo_sort[simulation.topo_start_idx:simulation.topo_start_idx + Simulation.INSTRUCTION_WINDOW_SIZE]
                        simulation.topo_start_idx += Simulation.INSTRUCTION_WINDOW_SIZE
                        simulation.b_topo_sort_changed = True  # Added to topo window

                assert len(simulation.priority_queue) > 0 or len(simulation.topo_sort) > 0, 'Possible infinite loop detected.'

                # Try to exhaust the priority queue first:
                # These may introduce some inefficiency to the schedule, but avoids
                # memory thrashing when new instructions become available from the topo sort
                xinstr = simulation.findNextInstructionToSchedule()
                fill_pq = not xinstr or xinstr.cycle_ready > simulation.current_cycle
                if fill_pq:
                    if simulation.b_topo_sort_changed or simulation.b_dependency_graph_changed:
                        # Extract all the instructions that can be executed without dependencies
                        # and merge to current instructions that can be executed without dependencies
                        last_idx = -1
                        for idx, instr_id in enumerate(simulation.topo_sort):
                            if instr_id in simulation.set_extracted_xinstrs:
                                last_idx = idx  # We want to remove repeated instructions
                            else:
                                assert instr_id in simulation.dependency_graph
                                if simulation.dependency_graph.in_degree(instr_id) > 0:
                                    # Found first instruction with dependencies
                                    last_idx = idx - 1
                                    break
                                instr = simulation.dependency_graph.nodes[instr_id]['instruction']
                                simulation.priority_queue_push(instr)
                                simulation.b_priority_queue_changed = True

                        # Remove all instructions that got queued for scheduling
                        if last_idx >= 0:
                            simulation.topo_sort = simulation.topo_sort[last_idx + 1:]
                            if xinstr:
                                # Next instruction to schedule may have changed after pulling from topo sort
                                simulation.priority_queue_push(xinstr)
                                xinstr = None

                        # Graph and topo sort have been updated
                        simulation.b_topo_sort_changed = False
                        simulation.b_dependency_graph_changed = False

                if xinstr or len(simulation.priority_queue) > 0:  # End do/while loop
                    # There must be, at least one instruction to schedule at this point
                    # (if condition was true),
                    # else, attempt to refill topo sort (restart the top of do/while loop)
                    break  # There is, at least, one instruction to schedule

            assert(len(simulation.xinsts_bundle) < simulation.max_bundle_size)  # We should have space in current bundle for an xinstruction

            # Find next xinstruction to schedule
            if not xinstr:
                assert(simulation.priority_queue)
                xinstr = simulation.findNextInstructionToSchedule()
            if not xinstr:
                # No instruction left to schedule this bundle

                # If this bundle is too short, attempt to bring instructions from
                # later bundles to schedule now, if possible
                if len(simulation.xinsts_bundle) <= simulation.BUNDLE_INSTRUCTION_MIN_LIMIT:
                    # Do not fix two short bundles in a row
                    if fixed_last_short_bundle + 1 < simulation.current_cycle.bundle:
                        # Do not fix if bank 0 is full
                        b_bundle_needs_fix = any(reg.contained_variable is None for reg in simulation.mem_model.register_banks[0])

                        if b_bundle_needs_fix:
                            # DEBUG
                            if GlobalConfig.debugVerbose:
                                print(f'---- Fixing short bundle {simulation.current_cycle.bundle}')
                            # ENDDEBUG

                            # Flush register banks and attempt to schedule again
                            for bank_idx in range(1, len(simulation.mem_model.register_banks)):
                                mem_utilities.flushRegisterBank(simulation.mem_model.register_banks[bank_idx],
                                                                simulation.current_cycle,
                                                                simulation.replacement_policy,
                                                                simulation.live_vars,
                                                                pct=0.5)
                            # Attempt to schedule instructions slated for next bundle in this bundle
                            tmp_set = set()
                            for _, xinstr in simulation.priority_queue:
                                if xinstr.cycle_ready.bundle == simulation.current_cycle.bundle + 1:
                                    if xinstr.cycle_ready.cycle <= 1:
                                        xinstr.cycle_ready = CycleType(bundle=simulation.current_cycle.bundle,
                                                                       cycle=xinstr.cycle_ready.cycle)
                                        tmp_set.add(xinstr)
                            for xinstr in tmp_set:
                                simulation.priority_queue_push(xinstr)
                            xinstr = simulation.findNextInstructionToSchedule()
                            fixed_last_short_bundle = simulation.current_cycle.bundle

                # Flush bundle anyway if no instruction was found after fixing
                b_flush_bundle = xinstr is None

            if not b_flush_bundle:
                assert(xinstr is not None)  # Only None if priority queue is empty

                # Attempt to schedule xinstruction

                # Scheduling logic:
                # - Block cstore locations in SPAD with dummy vars:
                #   * Add corresponding xstores to priority_queue and dependency graph with
                #     current xinstruction dependent on them (first xstore should replace current xinstruction to schedule).
                #   * If xmoves(target_bank, bank0) are required, they must be scheduled immediately.
                #   * Remove dependent xinstruction from priority_queue (make sure it is next in the topo_sort).
                # - All other cinsts and minsts before the bundle should be scheduled.
                # - Schedule all cstores after the bundle ifetch is scheduled (SPAD locations should be available because
                #   we blocked them in first step) (check that cstores can correctly allocate in SPAD with dummy var).
                # - Add all input and output variables to live_ins
                # - If xinstruction comes back from topo_sort it should not have pending dependencies, then schedule it.
                #   * Add all input and output variables to live_ins_used.
                ###############################################

                prep_counter = 0
                original_xinstr = xinstr
                while xinstr is not None:
                    # All xinstr at this point should be ready for current bundle

                    if GlobalConfig.debugVerbose:
                        if iter_counter % int(GlobalConfig.debugVerbose) == 0:
                            print('prep_counter', prep_counter)
                    xinstr_prepped, xinstr = prepareInstruction(original_xinstr, simulation)

                    if xinstr_prepped == 0:
                        assert xinstr is None
                        # Failed to prepare instruction in this bundle, leave it for next bundle
                        original_xinstr.cycle_ready = CycleType(bundle=simulation.current_cycle.bundle + 1,
                                                                cycle=0)
                        # Add back to priority queue
                        simulation.priority_queue_push(original_xinstr)
                    elif xinstr != original_xinstr:
                        # This is a preparation instruction
                        prep_counter += 1

                    if xinstr:
                        assert xinstr.id in simulation.dependency_graph
                        if simulation.dependency_graph.in_degree(xinstr.id) > 0:
                            # Instruction to schedule has new dependencies:
                            # This occurs if, while preparing the variables for the instruction,
                            # new dependencies were added.

                            assert xinstr == original_xinstr

                            xinstr = None

                        # Ready to schedule xinstruction
                        # Check if xinstruction is cycle ready for scheduling
                        elif xinstr.cycle_ready > simulation.current_cycle:

                            if prep_counter > 0:  # Instructions were added to prep original
                                if original_xinstr == xinstr:
                                    assert (xinstr_prepped == 1)
                                    # Original instruction prepped in this group, but not ready to schedule yet:
                                    # Put it back in the priority queue during schedule update phase
                                else:
                                    # Xinstr is not the original, but one needed to prepare the original

                                    assert not isinstance(xinstr, xinst.Move), f'xinstr = {repr(xinstr)} \ncycle = {simulation.current_cycle}; iter = {iter_counter}'

                                    # Cycle for xinstr is not ready yet, so,
                                    # put it back in the correct place in the simulation pipeline
                                    assert xinstr.id in simulation.dependency_graph \
                                        and simulation.dependency_graph.in_degree(xinstr.id) <= 0
                                    simulation.addXInstrBackIntoPipeline(xinstr)

                                # This will cause the schedule update phase below to put original instruction
                                # back in the correct place in the simulation pipeline (pq or topo sort)
                                xinstr = None

                            if xinstr:
                                assert prep_counter == 0
                                assert original_xinstr == xinstr

                                # Nop required
                                idle_cycles_required = xinstr.cycle_ready.cycle - simulation.current_cycle.cycle
                                if scheduleXNOP(xinstr,
                                                idle_cycles_required,
                                                simulation):
                                    simulation.total_idle_cycles += idle_cycles_required
                                else:
                                    # Could not schedule required NOP in this bundle:
                                    # Leave xinstruction for next bundle
                                    xinstr.cycle_ready = CycleType(bundle=simulation.current_cycle.bundle + 1,
                                                                  cycle=1)
                                    # Add back to pipeline during schedule update phase
                                    xinstr = None

                        if xinstr:
                            # We are still valid for scheduling

                            # At this point, xinstruction should be in ready cycle
                            assert(__canScheduleInBundle(xinstr, simulation, padding=0))
                            assert(simulation.current_cycle >= xinstr.cycle_ready)
                            # Simulate schedule of xinstruction
                            simulation.current_cycle += xinstr.schedule(simulation.current_cycle, len(simulation.xinsts_bundle) + 1)

                            # Mark the used lives
                            xinstr_var_names = set(v.name for v in xinstr.sources + xinstr.dests \
                                                if isinstance(v, Variable) and not isinstance(v, DummyVariable))
                            if isinstance(xinstr, xinst.XStore):
                                simulation.live_outs.update(xinstr_var_names)
                            for var_name in xinstr_var_names:
                                simulation.addUsedVar(var_name, xinstr)

                    # Schedule update phase
                    if xinstr:
                        # XInstruction scheduled: update remaining schedule
                        simulation.set_extracted_xinstrs.add(xinstr.id)
                        b_flush_bundle = simulation.updateSchedule(xinstr)
                        if original_xinstr == xinstr:
                            pisa_instr_counter += 1
                            if GlobalConfig.debugVerbose:
                                if iter_counter % int(GlobalConfig.debugVerbose) == 0:
                                    print(f'P-ISA scheduled: {pisa_instr_counter}')

                            # Check for completed outputs to flush
                            for variable in original_xinstr.dests:
                                # This assertion may be broken if move instructions end up back in the topo sort
                                assert(variable.name not in simulation.mem_model.store_buffer \
                                       or isinstance(original_xinstr, xinst.XStore))
                                if variable.name in simulation.mem_model.output_variables \
                                   and not variable.accessed_by_xinsts \
                                   and variable.name not in simulation.mem_model.store_buffer:
                                    # Variable is an output variable
                                    # and it is no longer needed
                                    # and it is not in-flight to be stored already
                                    if not simulation.flushOutputVariableFromRegister(variable):
                                        break  # Continue next bundle

                            # Terminate loop
                            xinstr = None
                        elif b_flush_bundle:
                            # Add back to priority queue if we haven't scheduled original yet
                            # and bundle needs to be flushed
                            simulation.addXInstrBackIntoPipeline(original_xinstr)
                            # Terminate loop
                            xinstr = None
                        elif simulation.priority_queue.find(simulation.current_cycle):
                            # Immediate instruction ready: stop preparing current
                            # Add back to pipeline if we haven't scheduled original yet
                            simulation.addXInstrBackIntoPipeline(original_xinstr)
                            # Terminate loop
                            xinstr = None

                    else:  # Xinstr was None
                        # Put original instruction back in the correct place of the simulation pipeline
                        simulation.addXInstrBackIntoPipeline(original_xinstr)

                if not simulation.dependency_graph:
                    # Completed schedule: store output variables still in registers
                    last_xinstr = simulation.last_xinstr
                    if not last_xinstr:
                        last_xinstr = original_xinstr
                    for output_var_name in simulation.mem_model.output_variables:
                        variable = simulation.mem_model.variables[output_var_name]
                        assert(not variable.accessed_by_xinsts)  # Variable should not be accessed any more
                        if not simulation.flushOutputVariableFromRegister(variable):
                            break  # Continue next bundle

            # Next cycle starts

        # Completed scheduling - first pass

        # Flush last bundle
        if len(simulation.xinsts_bundle) > 0:
            simulation.flushBundle()

        # Flush buffered xinstfetches to cinst
        if GlobalConfig.useXInstFetch:
            if len(simulation.xinstfetch_cinsts_buffer) > 0:
                simulation.cinsts = simulation.cinsts[:simulation.xinstfetch_location_idx_in_cinsts] \
                                    + simulation.xinstfetch_cinsts_buffer \
                                    + simulation.cinsts[simulation.xinstfetch_location_idx_in_cinsts:]

            # TODO:
            #################################
            warnings.warn("Rework xinstfetch logic to stream as XInsts are consumed instead of blindly placing them.")

        # End the CInst queue

        # Wait for last instruction in MInstQ to complete
        if len(simulation.minsts) > 0:
            last_csyncm = cinst.CSyncm(simulation.minsts[-1].id[0], simulation.minsts[-1])
            last_csyncm.schedule(simulation.current_cycle, len(simulation.cinsts) + 1)
            simulation.cinsts.append(last_csyncm)

        cexit = cinst.CExit(len(simulation.cinsts))
        cexit.schedule(simulation.current_cycle, len(simulation.cinsts) + 1)
        simulation.cinsts.append(cexit)

        # Rule: last instruction in MInstQ must be a sync pointing to cexit + 1
        last_msyncc = minst.MSyncc(cexit.id[0], cexit, comment='terminating MInstQ')
        last_msyncc.schedule(simulation.current_cycle, len(simulation.minsts) + 1)
        simulation.minsts.append(last_msyncc)

        # Completed scheduling - second pass

        # Corrects the sync instructions to point to correct instruction number
        simulation.updateQueuesSyncsPass2()

        if progress_verbose:
            print("100% - {0}/{0}".format(simulation.total_instructions))

    except KeyboardInterrupt as ex:
        if GlobalConfig.debugVerbose:
            cnt = 0
            while cnt < 10 and simulation.priority_queue:
                _, xinstr = simulation.priority_queue.pop()
                print('Cycle ready', xinstr.cycle_ready)
                print(repr(xinstr))
                cnt += 1
            if len(simulation.priority_queue) > 10:
                print('...')
            print('priority_queue', len(simulation.priority_queue))
            print('topo_sort', len(simulation.topo_sort))
            print('current cycle', simulation.current_cycle)
            simulation.mem_model.dump()

            import traceback
            traceback.print_exc()
            print(ex)
        else:
            raise

    return simulation.minsts, simulation.cinsts, simulation.xinsts, simulation.total_idle_cycles