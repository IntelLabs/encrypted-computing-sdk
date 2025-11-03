# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Utilities for grouping memory (.mem) variables into logical data splits.

This module offers a KernelSplitter class that:
  * Loads .mem files (memory map) via linker.instructions.dinst.create_from_mem_line
  * Extracts variable names from DLoad / DStore / DKeyGen instructions
  * Groups variables by: part, unit, rns-level, commons (shared variables)
  * Computes stats: total commons, per-group non-common counts, memory footprint
  * Use NetworkX algorithms to propose splits that fit within a memory size limit

Assumptions / Conventions:
  * Variable names follow a naming convention that encodes part, rns-level, unit.
  * Memory footprint per variable defaults to 1 unit (address slot) unless an
    external size map is provided.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from collections.abc import Iterable
from itertools import combinations
from pathlib import Path
from typing import TypeAlias

import networkx as nx
from assembler.common.config import GlobalConfig as Cfg
from assembler.common.dinst import DLoad, DStore, create_from_mem_line
from assembler.common.dinst.dinstruction import DInstruction
from assembler.instructions.xinst import NTT, Maci, iNTT, irShuffle, rShuffle, twiNTT, twNTT
from assembler.memory_model.variable import Variable

# Dict (var_name, producer_instr) -> Dict (consumer_set_id -> Set(consumer_instrs))
OutRefsMap: TypeAlias = dict[tuple[str, int], dict[int, set[int]]]


class KernelSplitter:
    """@brief Manage variable groupings & memory fitting strategies for .mem data."""

    def __init__(self):
        self._commons: set[str] = set()
        self._inputs: set[str] = set()
        self._outputs: set[str] = set()
        self._ext_vars: dict[int, set[str]] = {}  # Externals per instr id

    # -------------------------------------------------------------
    # Loading & extraction
    # -------------------------------------------------------------
    def load_mem_file(self, file_path: str | Path) -> list[DInstruction]:
        """
        @brief Load and decode a .mem file into data instructions.

        @param file_path Path or string pointing to the .mem source.
        @return Ordered list of parsed DInstruction instances.
        @throws FileNotFoundError When the provided path does not exist.
        @throws RuntimeError When a data line fails to parse.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f".mem file not found: {file_path}")

        dinstrs: list[DInstruction] = []
        append_instr = dinstrs.append
        add_input = self._inputs.add
        add_output = self._outputs.add
        register_common = self._register_common_var
        # Cache bound methods once so the tight parsing loop stays efficient for large .mem files.

        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue

                dinst = create_from_mem_line(raw)
                if not dinst:
                    raise RuntimeError(f"Error parsing line {line_no}: {raw}")

                append_instr(dinst)

                var_name = getattr(dinst, "var", None)
                if not var_name:
                    continue  # Instructions without named variables do not influence parsing.

                register_common(var_name)
                # Treat entries after the 12-line header as kernel I/O.
                if len(dinstrs) > 12:
                    if isinstance(dinst, DLoad):
                        add_input(var_name)
                    elif isinstance(dinst, DStore):
                        add_output(var_name)

        return dinstrs

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------
    def _is_common_var(self, var: str) -> bool:
        return bool(var) and var.startswith(("common", "ntt", "intt", "twid", "ones"))

    def _register_common_var(self, var: str) -> None:
        if self._is_common_var(var):
            self._commons.add(var)

    # -------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------
    @property
    def inputs(self) -> set[str]:
        return set(self._inputs)

    @property
    def outputs(self) -> set[str]:
        return set(self._outputs)

    @property
    def commons(self) -> set[str]:
        return set(self._commons)

    # -------------------------------------------------------------
    # Splitting logic
    # -------------------------------------------------------------
    def build_instrs_dependency_graph(self, insts: list) -> nx.DiGraph:
        """
        @brief Build a directed dependency graph between instructions based on variable flow.

        Nodes: instruction indices (0-based).
        Edges: from last source instruction to following destination instruction if they share a variable.
               Edge attribute 'var' stores the variable name causing the dependency.
               If multiple variables cause the same edge, they are appended to 'vars'.

        An instruction is expected to expose 'sources' and 'dests' lists whose elements
        have a 'name' attribute. Missing attributes are ignored.

        @param insts List of instruction objects (ordered).
        @return nx.DiGraph representing instruction dependencies.
        """
        G: nx.DiGraph = nx.DiGraph()
        G.add_nodes_from(range(len(insts)))

        last_writer: dict[str, int] = {}
        ext_in = self.inputs | self.commons
        ext_out = self.outputs | self.commons
        ext_vars = self._ext_vars  # local alias

        for idx, inst in enumerate(insts):
            if isinstance(inst, (NTT, iNTT, twNTT, twiNTT, rShuffle, irShuffle)):
                # NTT/iNTT/twNTT/twiNTT/rShuffle/irShuffle have implicit dependencies on all their dests and sources
                if idx + 1 < len(insts) and isinstance(insts[idx + 1], (NTT, iNTT, twNTT, twiNTT, rShuffle, irShuffle)):
                    G.add_edge(idx, idx + 1, weight=10)

            # Record external vars touched (sources)
            for var in inst.sources:
                name = var.name
                if not name:
                    continue
                if name in ext_in:
                    ext_vars.setdefault(idx, set()).add(name)
                writer = last_writer.get(name)
                if writer is not None and writer != idx:
                    weight_increment = 1
                    if isinstance(insts[writer], Maci) or (isinstance(inst, Maci) and name in inst.dests):
                        weight_increment = 5  # Prefer to keep Maci together with its producers/consumers

                    if G.has_edge(writer, idx):
                        var_set = G[writer][idx].setdefault("vars", set())
                        var_set.add(name)
                        G[writer][idx]["weight"] += weight_increment

                    else:
                        G.add_edge(writer, idx, vars={name}, weight=weight_increment)

            # Writes (destinations) update last_writer and mark external outputs
            for var in inst.dests:
                name = var.name
                if not name:
                    continue
                if name in ext_out:
                    ext_vars.setdefault(idx, set()).add(name)
                last_writer[name] = idx

        return G

    def split_mem_info(
        self,
        mem_path: str | Path,
        instrs: list[DInstruction],
        externals: list[set[str]],
        new_outs: list[dict[str, set[int]]] | None = None,
    ):
        """
        @brief Split a .mem file into multiple files based on provided external variable sets.

        @param mem_path (str | Path): Path to the original .mem file.
        @param instrs (list[DInstruction]): Instructions extracted from the original .mem file.
        @param externals (list[set[str]]): External variables required per split.
        @param new_outs (list[dict[str, set[int]]] | None): Optional map of new outputs per split.
        """

        commons = self._commons
        store_start = next((idx for idx, inst in enumerate(instrs) if isinstance(inst, DStore)), len(instrs))
        load_section = instrs[:store_start]
        store_section = instrs[store_start:]
        # Pre-slice load and store sections once so we avoid re-scanning instructions for every split.

        mem_path = Path(mem_path)
        root, ext = mem_path.stem, mem_path.suffix
        deps: dict[tuple[int, int], dict[int, int]] = {}
        active_vars: dict[str, tuple[int, set[int]]] = {}

        for idx, ext_vars in enumerate(externals):
            output_mem_fname = mem_path.parent / f"{root}_{idx}{ext}"
            pending_outs = new_outs[idx] if new_outs and idx < len(new_outs) else None

            def include_var(name: str | None, ext_vars: set[str]) -> bool:
                return bool(name) and (name in ext_vars or name in commons)

            with output_mem_fname.open("w", encoding="utf-8") as f:
                new_spad_address = 0

                for dinstr in load_section:
                    var_name = getattr(dinstr, "var", None)
                    if not include_var(var_name, ext_vars):
                        continue
                    dinstr.address = new_spad_address
                    f.write(f"{dinstr.to_line()}\n")
                    new_spad_address += 1

                # New inputs from active vars
                for var, (address, prod, refs) in tuple(active_vars.items()):
                    if idx not in refs:
                        continue
                    dinstr = DLoad(tokens=[DLoad.name, "poly", new_spad_address, var], comment="")
                    deps.setdefault((prod, idx), {}).setdefault(address, new_spad_address)
                    f.write(f"{dinstr.to_line()}\n")
                    new_spad_address += 1
                    refs.discard(idx)
                    if not refs:
                        active_vars.pop(var, None)

                for dinstr in store_section:
                    var_name = getattr(dinstr, "var", None)
                    if not include_var(var_name, ext_vars):
                        continue
                    dinstr.address = new_spad_address
                    f.write(f"{dinstr.to_line()}\n")
                    new_spad_address += 1

                # New outputs from pending outs
                if pending_outs:
                    for var in sorted(pending_outs):
                        refs = pending_outs[var]
                        active_vars[var] = (new_spad_address, idx, refs)
                        dinstr = DStore(tokens=[DStore.name, var, new_spad_address], comment="")
                        dinstr.address = new_spad_address
                        f.write(f"{dinstr.to_line()}\n")
                        new_spad_address += 1

        self._write_dependency_maps(mem_path, root, range(len(externals)), deps)

    def _write_dependency_maps(
        self,
        mem_path: Path,
        root: str,
        sets: list[int],
        deps: dict[tuple[int, int], dict[int, int]],
    ) -> None:
        """
        @brief Persist inter-split dependency address mappings as JSON files.

        @param mem_path Base path of the original .mem file.
        @param root Stem used to generate per-split dependency filenames.
        @param sets Iterable of split identifiers to emit dependency maps for.
        @param deps Lookup from (producer_split, consumer_split) to address remap dictionaries.
        """
        for i in sets:
            dep_map_file_name = mem_path.parent / f"{root}_deps_{i}.json"
            addr_to_set_addr: dict[int, dict[int, int]] = {}
            for j in range(i + 1, len(sets)):
                for spad_addr, target_addr in deps.get((i, j), {}).items():
                    addr_to_set_addr.setdefault(spad_addr, {})[j] = target_addr
            with dep_map_file_name.open("w", encoding="utf-8") as map_f:
                json.dump(addr_to_set_addr, map_f, indent=2)

    def get_isolated_instrs_splits(
        self,
        graph: nx.DiGraph,
        instr_limit: int,
        spad_limit: int,
    ) -> tuple:
        """
        @brief Partition disconnected instruction components under resource limits.

        @param graph Instruction dependency graph whose connected components are evaluated.
        @param insts Original instruction list (kept for signature parity with other helpers).
        @param instr_limit Maximum number of instructions allowed per split.
        @param spad_limit Maximum external memory footprint permitted per split.
        @return Tuple (list of instruction-id sets, list of external-var sets) or (None, None) if limits cannot be met.
        """
        node_count = graph.number_of_nodes()
        if node_count == 0:
            return [], []

        components = list(nx.connected_components(graph.to_undirected()))
        if Cfg.debugVerbose > 0:
            print(f"Found {len(components)} isolated components in dependency graph.")

        if not components:
            return [], []

        final_split_instrs: list[set[int]] = []
        externals: list[set[str]] = []
        working_split: set[int] = set()
        working_externals: set[str] = set()

        for component in components:
            candidate_split = working_split | component if working_split else set(component)
            candidate_mem, candidate_ext = self._get_external_mem_usage(candidate_split)
            overflow = len(candidate_split) > instr_limit or candidate_mem > spad_limit

            if overflow:
                if not working_split:
                    return None, None
                final_split_instrs.append(set(working_split))
                externals.append(set(working_externals))
                working_split.clear()
                working_externals.clear()
                candidate_split = set(component)
                candidate_mem, candidate_ext = self._get_external_mem_usage(candidate_split)
                if len(candidate_split) > instr_limit or candidate_mem > spad_limit:
                    return None, None

            working_split.update(candidate_split)
            working_externals.update(candidate_ext)

        if working_split:
            final_split_instrs.append(set(working_split))
            externals.append(set(working_externals))

        total_instrs = sum(len(s) for s in final_split_instrs)
        if total_instrs == node_count:
            if Cfg.debugVerbose > 0:
                print("\n--- Final Isolated Splits Summary ---\n")
            for set_id, instr_set in enumerate(final_split_instrs):
                ext_mem_usage, exts = self._get_external_mem_usage(instr_set)
                externals[set_id] = exts
                if Cfg.debugVerbose > 0:
                    print(
                        f"Instruction set {set_id:03d}: \tTotal Intructions: {len(instr_set):03d} - " f"\tTotal Externals ({ext_mem_usage})"
                    )
            return final_split_instrs, externals

        return None, None

    def get_community_instrs_splits(
        self,
        graph: nx.DiGraph,
        instr_limit: int,
        spad_limit: int,
    ) -> tuple:
        """
        @brief Build instruction splits using community detection and merging constraints.

        @param graph Dependency graph whose nodes represent instructions.
        @param instr_limit Maximum instructions allowed per resulting split.
        @param spad_limit Maximum shared-memory footprint permitted per split.
        @return Tuple containing (splits, external variable sets, outbound reference maps) or raises on failure.
        """

        node_count = graph.number_of_nodes()
        if graph.number_of_edges() > 0:
            undirected = graph.to_undirected()
            communities = list(nx.community.greedy_modularity_communities(undirected, weight="weight"))
        elif node_count > 0:
            communities = [{node} for node in graph.nodes]
        else:
            return None, None, None

        if Cfg.debugVerbose > 0:
            print(f"Found {len(communities)} weakly isolated communities in dependency graph.")

        # Prepare community graph
        instr_sets, metaG = self._prepare_community_graph(graph, communities)
        if Cfg.debugVerbose > 0:
            print(f"Got {len(instr_sets)} communities after condensing and preparing.")

        # First stage: in-generation merges
        sorted_communities, new_instr_sets, new_split_ids = self._in_generation_merge(
            metaG,
            instr_sets,
            instr_limit,
            spad_limit,
        )

        # Second stage: cross-generation merges
        final_split_instrs, final_outs_refs, final_split_ids = self._greedy_community_merge(
            metaG, sorted_communities, new_instr_sets, new_split_ids, instr_limit, spad_limit
        )

        # Validation
        total_instrs = sum(len(s) for s in final_split_instrs) if final_split_instrs else 0
        if total_instrs != node_count:
            raise RuntimeError("Final instruction splits do not cover all instructions.")

        if Cfg.debugVerbose > 0:
            print("\n--- Final Splits Summary ---\n")

        # Capture external usage per split
        externals: list[set[str]] = []
        get_external_usage = self._get_external_mem_usage  # Avoid repeated dict lookups in tight loops
        get_inout_usage = self._get_inout_mem_usage
        for set_id, instr_set in enumerate(final_split_instrs):
            ext_mem_usage, exts = get_external_usage(instr_set)
            mem_usage, _ = get_inout_usage(final_split_ids[set_id], metaG, exts)
            externals.append(exts)
            if Cfg.debugVerbose > 0:
                print(
                    f"Instruction set {set_id:03d}: \tTotal Intructions: {len(instr_set):03d} - "
                    f"\tTotal Vars: {ext_mem_usage + mem_usage} = Externals ({ext_mem_usage}) + New Internal Deps ({mem_usage})"
                )

        return final_split_instrs, externals, final_outs_refs

    def prepare_instruction_splits(self, args, insts_listing: list) -> list[tuple[list[int], str]]:
        """
        @brief Execute the full instruction-splitting pipeline and persist split artifacts.

        @param args Namespace carrying runtime options (mem file, output path, verbose flags).
        @param insts_listing Instruction sequence to partition across splits.

        @return Tuple with (sub_kernels ready for emission); each entry is (inst_list, output_path).
        """
        dinstrs = self.load_mem_file(args.mem_file)
        instrs_graphs = self.build_instrs_dependency_graph(insts_listing)

        if Cfg.debugVerbose > 0:
            print(f"Parsed ({len(insts_listing)}) instructions, splitting...")
            print(f"Total inputs/outputs: {len(self.inputs) + len(self.outputs)}")
            print(f"Common variables: {len(self.commons)} -> {sorted(self.commons)}")

        instr_sets, externals = self.get_isolated_instrs_splits(instrs_graphs, args.split_inst_limit, args.split_vars_limit)
        out_refs: list[OutRefsMap] = []
        if instr_sets is None:
            if Cfg.debugVerbose > 0:
                print("Falling back to community-based splitting...")
            instr_sets, externals, out_refs = self.get_community_instrs_splits(instrs_graphs, args.split_inst_limit, args.split_vars_limit)
            if instr_sets is None:
                raise RuntimeError("Could not split instructions into sets that fit memory constraints.")

        new_out_refs = self.rename_vars_in_splits(insts_listing, instr_sets, out_refs)
        self.split_mem_info(args.mem_file, dinstrs, externals, new_out_refs)

        root, ext = os.path.splitext(args.output_file_name)
        sub_kernels: list[tuple[list[int], str]] = []
        for inst_idx, instr_set in enumerate(instr_sets):
            split_output_file_name = root + f"_{inst_idx}" + ext
            split_insts_listing: list[int] = []
            for idx in sorted(instr_set):
                split_insts_listing.append(insts_listing[idx])
            sub_kernels.append((split_insts_listing, split_output_file_name))

        # Debug: Save one kernel with split IDs
        if Cfg.debugVerbose > 2:
            root, ext = os.path.splitext(args.output_file_name)
            debug_output_file = root + "_debug" + ext
            print(f"Saving debug output with split IDs to {debug_output_file}")
            with open(debug_output_file, "w", encoding="utf-8") as outnum:
                for idx, inst in enumerate(insts_listing):
                    inst_line = inst.to_pisa_format()
                    split_id = -1
                    for set_id, split in enumerate(instr_sets):
                        if idx in split:
                            split_id = set_id
                            break
                    if inst_line:
                        print(f"{split_id}:{idx} {inst_line}", file=outnum)

        return sub_kernels

    def _get_external_mem_usage(
        self,
        instr_set: set[int],
        var_size_map: dict[str, int] | None = None,
    ) -> tuple[int, set[str]]:
        """
        @brief Compute memory usage for in/out variables used in a split.

        @param instr_set Instruction indices assigned to the current split.
        @param var_size_map Optional mapping with per-variable memory footprints.
        @return Pair of (total memory units, external variable set).
        """
        var_size_map = var_size_map or {}
        get_size = var_size_map.get
        commons = self._commons
        external_vars: set[str] = set()

        ext_lookup = self._ext_vars.get  # Cache lookup to avoid repeating dict hits in the loop.
        for instr in instr_set:
            refs = ext_lookup(instr)
            if refs:
                external_vars.update(refs)

        if not external_vars and not commons:
            return 0, external_vars

        vars_used = set(external_vars)
        if commons:
            vars_used.update(commons)

        total_mem = sum(int(get_size(var, 1)) for var in vars_used)
        return total_mem, external_vars

    def _get_inout_mem_usage(
        self,
        set_ids: list[int],
        graph: nx.DiGraph,
        external_vars: set[str],
        var_size_map: dict[str, int] | None = None,
    ) -> tuple[int, OutRefsMap]:
        """
        @brief Measure boundary memory needs for a collection of communities.

        @param set_ids Community identifiers grouped into the current split.
        @param graph Community-level dependency graph carrying var_refs metadata.
        @param external_vars Variables already counted as external for the split.
        @param var_size_map Optional per-variable footprint overrides.
        @return Pair of (total boundary memory units, outbound reference map).
        """
        var_size_map = var_size_map or {}
        get_size = var_size_map.get
        tracked_sets = set(set_ids)
        external_lookup = external_vars.__contains__  # Cache membership check for tight loops.
        inout_vars: set[str] = set()
        outs_refs: OutRefsMap = {}
        for set_id in tracked_sets:
            # Ins
            for p_set, c_set, data in graph.in_edges(set_id, data=True):
                if c_set in tracked_sets and p_set not in tracked_sets:
                    for p_instr, _, var in data.get("var_refs") or ():
                        if not external_lookup(var):
                            key = (var, p_instr)
                            inout_vars.add(key)
            # Outs
            for p_set, c_set, data in graph.out_edges(set_id, data=True):
                if p_set in tracked_sets and c_set not in tracked_sets:
                    for p_instr, c_instr, var in data.get("var_refs") or ():
                        key = (var, p_instr)
                        per_consumer = outs_refs.setdefault(key, {})
                        per_consumer.setdefault(c_set, set()).add(c_instr)
                        if not external_lookup(var):
                            inout_vars.add(key)

        total_mem = sum(int(get_size(var, 1)) for var in inout_vars)
        return total_mem, outs_refs

    def _map_instr_to_community(self, communities: list[set[int]]) -> dict[int, int]:
        """
        @brief Produce a lookup from instruction id to its community index.

        @param communities Collection of instruction id sets grouped per community.
        @return Dictionary mapping each instruction id to the index of its containing community.
        """
        instr_to_set: dict[int, int] = {}
        for sid, group in enumerate(communities):
            for instr in group:
                instr_to_set[instr] = sid
        return instr_to_set

    def _build_community_graph(
        self,
        base_graph: nx.DiGraph,
        communities: list[set[int]],
        instr_to_set: dict[int, int],
    ) -> nx.DiGraph:
        """
        @brief Build a community-level graph with variable flow metadata.

        @param base_graph Instruction-level dependency graph.
        @param communities List of instruction id sets per community.
        @param instr_to_set Mapping from instruction id to its community index.
        @return Directed graph whose edges carry aggregated var references between communities.
        """
        CG: nx.DiGraph = nx.DiGraph()
        CG.add_nodes_from(range(len(communities)))
        # Track variables overwritten inside a community so inbound edges using those vars can be ignored.
        overwritten: defaultdict[int, set[str]] = defaultdict(set)
        # Accumulate cross-community references before mutating the graph to avoid repeated edge updates.
        edge_acc: dict[tuple[int, int], set[tuple[int, int, str]]] = defaultdict(set)

        for idx in sorted(instr_to_set):
            set_id = instr_to_set[idx]
            community_nodes = communities[set_id]
            filtered = overwritten[set_id]

            for prod, cons, data in base_graph.in_edges(idx, data=True):
                p_set = instr_to_set.get(prod)
                if p_set is None or prod in community_nodes:
                    continue
                for var in data.get("vars") or ():
                    if var in filtered:
                        continue
                    edge_acc[(p_set, set_id)].add((prod, cons, var))

            for prod, cons, data in base_graph.out_edges(idx, data=True):
                c_set = instr_to_set.get(cons)
                if c_set is None:
                    continue
                vars_iter = data.get("vars") or ()
                if cons in community_nodes:
                    filtered.update(vars_iter)
                    continue
                for var in vars_iter:
                    edge_acc[(set_id, c_set)].add((prod, cons, var))

        # Emit aggregated edges once per community pair, updating weights using the total reference count.
        for (src, dst), refs in edge_acc.items():
            weight = len(refs) or 1
            if CG.has_edge(src, dst):
                edge_data = CG[src][dst]
                var_refs = edge_data.setdefault("var_refs", set())
                var_refs.update(refs)
                edge_data["weight"] = len(var_refs)
            else:
                CG.add_edge(src, dst, var_refs=set(refs), weight=weight)

        return CG

    def _condense_community_graph(
        self,
        graph: nx.DiGraph,
        communities: list[set[int]],
    ) -> tuple[list[set[int]], nx.DiGraph]:
        """
        @brief Collapse strongly connected communities into a DAG while keeping edge metadata.

        @param graph Community-level graph that may contain cycles.
        @param communities Instruction index sets grouped per community.
        @return Tuple with merged instruction sets, condensed DAG, and its topological order.
        """
        cond_graph = nx.condensation(graph)
        mapping: dict[int, int] = cond_graph.graph.get("mapping", {})

        # Collect outgoing edge metadata per condensed pair so we can reattach it later.
        edge_acc: dict[tuple[int, int], set] = defaultdict(set)
        for u, v, data in graph.edges(data=True):
            cond_u, cond_v = mapping[u], mapping[v]
            if cond_u == cond_v:
                continue
            edge_acc[(cond_u, cond_v)].update(data.get("var_refs", ()))

        # Reapply metadata onto the condensed graph, updating weights accordingly.
        for (cond_u, cond_v), var_refs in edge_acc.items():
            weight = len(var_refs) or 1
            if cond_graph.has_edge(cond_u, cond_v):
                edge_data = cond_graph[cond_u][cond_v]
                edge_vars = edge_data.setdefault("var_refs", set())
                edge_vars.update(var_refs)
                edge_data["weight"] = len(edge_vars) or weight
            else:
                cond_graph.add_edge(cond_u, cond_v, var_refs=set(var_refs), weight=weight)

        # Group original community ids per condensed component to rebuild instruction sets.
        comp_members: dict[int, set[int]] = defaultdict(set)
        for orig, comp_id in mapping.items():
            comp_members[comp_id].add(orig)

        # Get new instruction sets per condensed component.
        new_instr_sets = [{instr for member in members for instr in communities[member]} for _, members in sorted(comp_members.items())]

        return (new_instr_sets if new_instr_sets else communities), cond_graph

    def _prepare_community_graph(
        self,
        graph: nx.DiGraph,
        communities: list[set[int]],
    ) -> tuple[list[set[int]], nx.DiGraph]:
        """
        @brief Build the community-level dependency graph, condensing SCC cycles when required.

        @param graph Directed instruction dependency graph.
        @param communities List of instruction index sets representing detected communities.
        @return Tuple of (per-community instruction sets, community dependency graph, topological order of communities).
        """
        if not communities:
            return [], nx.DiGraph(), []

        instr_to_set = self._map_instr_to_community(communities)
        CG = self._build_community_graph(graph, communities, instr_to_set)

        if nx.is_directed_acyclic_graph(CG):
            return communities, CG

        return self._condense_community_graph(CG, communities)

    def _in_generation_merge(
        self,
        meta_graph: nx.DiGraph,
        instr_sets: dict[int, set[int]],
        instr_limit: int,
        spad_limit: int,
    ) -> tuple[list[int], dict[int, set[int]], dict[int, set[int]]]:
        """
        @brief Merge communities generation-by-generation while honoring resource limits.

        @param meta_graph Community-level dependency graph.
        @param instr_sets Mapping from community id to its instruction indices.
        @param instr_limit Maximum instructions permitted per merged cluster.
        @param spad_limit Maximum external memory footprint permitted per merged cluster.
        @return Tuple containing the merged community order, instruction sets, and membership map.
        """
        generations = list(nx.algorithms.dag.topological_generations(meta_graph))
        if Cfg.debugVerbose > 0:
            print(" Generations: ")
            for gen_id, gen in enumerate(generations):
                print(f"  Generation {gen_id}: {sorted(gen)}")

        new_sorted: list[int] = []
        new_instr_sets: dict[int, set[int]] = {}
        new_split_ids: dict[int, set[int]] = {}

        for generation in generations:
            # Rank pairs within the generation by their common I/O.
            ranked_pairs = self._rank_generation_pairs_by_common_io(meta_graph, generation)
            working_pairs = ranked_pairs.copy()

            # Initialize each community as its own cluster.
            cluster_map: dict[int, int] = {sid: sid for sid in generation}
            cluster_sets: dict[int, set[int]] = {sid: {sid} for sid in generation}
            cluster_instrs: dict[int, set[int]] = {sid: set(instr_sets[sid]) for sid in generation}

            merged_any = True
            while merged_any:
                merged_any = False

                # Prepare non-overlapping pairs for this iteration.
                used_nodes: set[int] = set()
                filtered_pairs: list[tuple[int, int]] = []
                for left, right in working_pairs:
                    if left not in used_nodes and right not in used_nodes:
                        filtered_pairs.append((left, right))
                        used_nodes.add(left)
                        used_nodes.add(right)

                # Attempt merges for each candidate pair.
                for left, right in filtered_pairs:
                    rep_left = cluster_map.get(left)
                    rep_right = cluster_map.get(right)
                    if rep_left is None or rep_right is None or rep_left == rep_right:
                        continue

                    candidate_set_ids = cluster_sets[rep_left] | cluster_sets[rep_right]
                    candidate_instrs = cluster_instrs[rep_left] | cluster_instrs[rep_right]

                    if len(candidate_instrs) > instr_limit:
                        continue

                    # Check memory usage
                    ext_mem_usage, externals = self._get_external_mem_usage(candidate_instrs)
                    inouts_mem_usage, _ = self._get_inout_mem_usage(sorted(candidate_set_ids), meta_graph, externals)
                    if (ext_mem_usage + inouts_mem_usage) > spad_limit:
                        continue

                    # Merge clusters
                    merged_any = True
                    new_rep = min(candidate_set_ids)
                    cluster_sets[new_rep] = set(candidate_set_ids)
                    cluster_instrs[new_rep] = set(candidate_instrs)

                    # Update cluster map
                    for member in candidate_set_ids:
                        cluster_map[member] = new_rep

                    # Remove old clusters
                    for old_rep in {rep_left, rep_right}:
                        if old_rep != new_rep:
                            cluster_sets.pop(old_rep, None)
                            cluster_instrs.pop(old_rep, None)

                # Re-rank remaining pairs based on merged clusters.
                working_pairs = self._rebuild_generation_pairs(cluster_sets, ranked_pairs)

            # Emit merged clusters from this generation
            for rep in cluster_sets.keys():
                new_sorted.append(rep)
                new_instr_sets[rep] = cluster_instrs[rep]
                new_split_ids[rep] = cluster_sets[rep]

        return new_sorted, new_instr_sets, new_split_ids

    def _greedy_community_merge(
        self,
        meta_graph: nx.DiGraph,
        ordered_communities: list[int],
        instr_sets: dict[int, set[int]],
        split_ids: dict[int, set[int]],
        instr_limit: int,
        spad_limit: int,
    ) -> tuple | tuple[None, None, None]:
        """
        @brief Greedily pack merged communities into instruction splits under resource constraints.

        @param meta_graph Community-level dependency DAG tracking variable crossings.
        @param ordered_communities Communities sorted according to generation merge order.
        @param instr_sets Mapping from community id to its instruction indices.
        @param split_ids Mapping from community id to original community members per merge.
        @param instr_limit Maximum instructions allowed in each final split.
        @param spad_limit Maximum shared-memory footprint allowed per split.
        @return Tuple with (instruction splits, outbound reference maps, community membership sets) or failure tuple.
        """
        final_split_instrs: list[set[int]] = []
        final_outs_refs: list[OutRefsMap] = []
        final_split_ids: list[set[int]] = []

        t_refs: OutRefsMap = {}
        t_split: set[int] = set()
        t_set_ids: list[int] = []

        get_external_usage = self._get_external_mem_usage
        get_inout_usage = self._get_inout_mem_usage

        idx: int = 0
        while idx < len(ordered_communities):
            set_id = ordered_communities[idx]
            new_instrs = instr_sets[set_id]
            new_ids = list(split_ids[set_id])

            candidate_split = t_split.union(new_instrs) if t_split else set(new_instrs)
            if len(candidate_split) > instr_limit:
                if not t_split:
                    break
                final_split_instrs.append(set(t_split))
                final_split_ids.append(set(t_set_ids))
                final_outs_refs.append(t_refs)
                t_split.clear()
                t_set_ids.clear()
                t_refs = {}
                continue

            candidate_ids = t_set_ids + new_ids
            ext_mem_usage, externals = get_external_usage(candidate_split)
            inouts_mem_usage, out_refs = get_inout_usage(candidate_ids, meta_graph, externals)
            if (ext_mem_usage + inouts_mem_usage) > spad_limit:
                if not t_split:
                    break
                final_split_instrs.append(set(t_split))
                final_split_ids.append(set(t_set_ids))
                final_outs_refs.append(t_refs)
                t_split.clear()
                t_set_ids.clear()
                t_refs = {}
                continue

            t_split = candidate_split
            t_set_ids = candidate_ids
            t_refs = out_refs
            idx += 1

        if t_split:
            final_split_instrs.append(t_split)
            final_split_ids.append(set(t_set_ids))
            final_outs_refs.append(t_refs)

        # Update outbound references to reflect new split indices
        for new_set_id_i, ref in enumerate(final_outs_refs):
            future_splits = list(enumerate(final_split_ids[new_set_id_i + 1 :], start=new_set_id_i + 1))
            for key, consumer_sets in ref.items():
                new_mapping: dict[int, set[int]] = {}
                for future_set_id, future_members in future_splits:
                    relevant_old_sets = future_members.intersection(consumer_sets)
                    if not relevant_old_sets:
                        continue
                    combined_instrs: set[int] = set()
                    for old_set_id in relevant_old_sets:
                        combined_instrs.update(consumer_sets[old_set_id])
                    if combined_instrs:
                        new_mapping[future_set_id] = combined_instrs
                ref[key] = new_mapping

        return final_split_instrs, final_outs_refs, final_split_ids

    def rename_vars_in_splits(
        self,
        insts_listing: list,
        instr_sets: list[set[int]],
        out_refs: list[OutRefsMap],
    ) -> list[dict[str, set[int]]]:
        """
        @brief Rename boundary variables within each split and register downstream split consumers.

        @param insts_listing Ordered kernel instruction list being rewritten in-place.
        @param instr_sets Instruction indices per split emitted by the split planner.
        @param out_refs Per-split outbound usage tables keyed by (var_name, producer_idx).
        @return List mapping each generated variable name to the set of consumer split ids.
        """
        if not out_refs:
            return []

        def _replace_sources(instr, old_name, new_var):
            # Swap every source operand matching old_name with the new split-local variable.
            instr.sources = [new_var if src.name == old_name else src for src in instr.sources]

        new_outs: list[dict[str, set[int]]] = []
        for set_id, split_out_refs in enumerate(out_refs):
            if not split_out_refs:
                new_outs.append({})
                continue

            # Build fast lookup for instruction positions inside the split.
            set_instrs = sorted(instr_sets[set_id])
            in_split_idx = {inst_idx: pos for pos, inst_idx in enumerate(set_instrs)}
            consumers_per_var: dict[str, set[int]] = {}

            for (var_name, producer_idx), consumers in split_out_refs.items():
                # Emit the split-scoped variable name and rewrite the producer’s destinations.
                new_var_name = f"{var_name}_dep_{set_id}_{producer_idx}"
                producer_instr = insts_listing[producer_idx]

                new_var = None
                new_dests = []
                for dest in producer_instr.dests:
                    if dest.name == var_name:
                        new_var = Variable(new_var_name, dest.suggested_bank)
                        new_dests.append(new_var)
                    else:
                        new_dests.append(dest)
                producer_instr.dests = new_dests
                if new_var is None:
                    new_var = Variable(new_var_name, None)

                # Propagate renaming forward until the value is overwritten or exported again.
                start = in_split_idx.get(producer_idx, -1) + 1
                while 0 <= start < len(set_instrs):
                    instr_idx = set_instrs[start]
                    instr = insts_listing[instr_idx]
                    _replace_sources(instr, var_name, new_var)

                    key_instr_idx = (var_name, instr_idx)
                    key_position = (var_name, start)
                    if key_instr_idx in split_out_refs or key_position in split_out_refs:
                        break
                    if any(dest.name == var_name for dest in instr.dests):
                        break
                    start += 1

                # Record consumers in downstream splits and rewrite their sources.
                var_consumers = consumers_per_var.setdefault(new_var_name, set())
                for consumer_set_id, consumer_instrs in consumers.items():
                    for instr_idx in consumer_instrs:
                        _replace_sources(insts_listing[instr_idx], var_name, new_var)
                    var_consumers.add(consumer_set_id)

            new_outs.append(consumers_per_var)

        return new_outs

    def _rank_generation_pairs_by_common_io(
        self,
        graph: nx.DiGraph,
        generation: Iterable[int],
    ) -> dict[tuple[int, int], float]:
        """
        @brief Rank generation node pairs by shared weighted predecessors/successors.

        @param graph Directed community graph describing dependencies between generation nodes.
        @param generation Iterable of community identifiers belonging to the same topological generation.
        @return Dictionary mapping ordered node pairs to their aggregated shared I/O weight score (descending order).
        """
        nodes = sorted(set(generation))
        scores: dict[tuple[int, int], float] = {}
        if len(nodes) < 2:
            return scores

        # Precompute to avoid repeated graph lookups.
        pred_sets = {node: set(graph.predecessors(node)) for node in nodes}
        pred_weights = {node: {pred: graph[pred][node].get("weight", 1) for pred in preds} for node, preds in pred_sets.items()}
        succ_sets = {node: set(graph.successors(node)) for node in nodes}
        succ_weights = {node: {succ: graph[node][succ].get("weight", 1) for succ in succs} for node, succs in succ_sets.items()}

        # Increment scores based on shared predecessors and successors.
        for left, right in combinations(nodes, 2):
            score = 0.0
            for pred in pred_sets[left] & pred_sets[right]:
                score += min(pred_weights[left][pred], pred_weights[right][pred])
            for succ in succ_sets[left] & succ_sets[right]:
                score += min(succ_weights[left][succ], succ_weights[right][succ])
            scores[(left, right)] = score

        sorted_pairs = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        return dict(sorted_pairs)

    def _rebuild_generation_pairs(
        self,
        cluster_sets: dict[int, set[int]],
        ranked_pairs: dict[tuple[int, int], float],
    ) -> dict[tuple[int, int], float]:
        """
        @brief Recompute the candidate merge pairs and their scores after cluster updates.

        @param cluster_sets Mapping from cluster representative to its member community identifiers.
        @param ranked_pairs Precomputed scores keyed by ordered community pairs used for tie-breaking.
        @return Dictionary of (clusterA, clusterB) -> score sorted by descending score.
        """
        new_working_pairs: dict[tuple[int, int], float] = {}
        for left, right in combinations(cluster_sets, 2):
            left_members = cluster_sets[left]
            right_members = cluster_sets[right]
            score = 0.0
            for lm in left_members:
                for rm in right_members:
                    key = (lm, rm) if lm < rm else (rm, lm)
                    score += ranked_pairs.get(key, 0.0)
            new_working_pairs[(left, right)] = score
        sorted_pairs = sorted(new_working_pairs.items(), key=lambda item: item[1], reverse=True)
        return dict(sorted_pairs)


__all__ = ["KernelSplitter"]
