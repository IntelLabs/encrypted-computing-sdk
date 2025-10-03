"""@brief Utilities for grouping memory (.mem) variables into logical data splits.

This module offers a DataSplits class that:
  * Loads .mem files (memory map) via linker.instructions.dinst.create_from_mem_line
  * Extracts variable names from DLoad / DStore / DKeyGen instructions
  * Groups variables by: part, unit, rns-level, commons (shared variables)
  * Computes stats: total commons, per-group non-common counts, memory footprint
  * Use NetworkX algorithms to propose splits that fit within a memory size limit

Assumptions / Conventions:
  * Variable names follow a naming convention that encodes part, rns-level, unit.
  * Memory footprint per variable defaults to 1 unit (address slot) unless an
    external size map is provided.
  * The user can supply a custom parser callback to override the default
    naming rule.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import networkx as nx
from linker.instructions.dinst import DLoad, DStore, create_from_mem_line
from linker.instructions.dinst.dinstruction import DInstruction

# Type aliases
VarName = str
GroupName = str

VarParseFn = Callable[[VarName], tuple[str | None, str | None, str | None, bool]]
# Returns: (part, rns_level, unit, is_common)


def _default_var_parse(var_name: str) -> tuple[str | None, str | None, str | None, str | None, bool]:
    """@brief Default parser to infer (part, rns-level, unit, is_common) from a variable name.

    Heuristics:
      * Variables starting with 'common' => common
      * Split by '_' and map:
          token[0] -> part
          token[1] -> rns-level
          token[2] -> unit
    """
    if not var_name:
        return (None, None, None, False)
    is_common = var_name.startswith(("common", "ntt", "intt", "twid", "ones"))
    if is_common:
        return (None, None, None, True)

    toks = var_name.split("_")
    part = toks[-3] if len(toks) >= 3 else None
    rns = toks[-2] if len(toks) >= 2 else None
    unit = toks[-1] if len(toks) >= 1 else None
    return (part, rns, unit, is_common)


class DataSplits:
    """@brief Manage variable groupings & memory fitting strategies for .mem data.

    Public workflow:
        ds = DataSplits()
        ds.load_mem_file("program.mem")
        stats = ds.compute_stats()
        splits = ds.propose_splits(memory_limit=128)

    Custom parsing:
        ds = DataSplits(parser=my_parse_fn)
    """

    def __init__(self, parser: VarParseFn | None = None):
        self._var_parser: VarParseFn = parser or _default_var_parse
        self._variables: set[VarName] = set()
        self._commons: set[VarName] = set()
        self._inputs: set[str] = set()
        self._outputs: set[str] = set()
        self._ext_vars: dict[int, set[str]] = {}

    # -------------------------------------------------------------
    # Loading & extraction
    # -------------------------------------------------------------
    def load_mem_file(self, file_path: str | Path) -> list:
        """@brief Load a .mem file and accumulate variable grouping information.

        Ignores blank lines and pure comment lines. Any parse failure raises a RuntimeError.
        """
        dinstrs: list = []
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f".mem file not found: {file_path}")

        with path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue

                dinst = create_from_mem_line(raw)

                if not dinst:
                    raise RuntimeError(f"Error parsing line {idx + 1}: {raw}")
                dinstrs.append(dinst)

                if idx > 12:
                    if isinstance(dinst, DLoad):
                        self._inputs.add(dinst.var)
                    if isinstance(dinst, DStore):
                        self._outputs.add(dinst.var)

                self._register_variable(dinst.var)

        return dinstrs

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------
    def _register_variable(self, var: VarName) -> None:
        _, _, _, is_common = self._var_parser(var)
        self._variables.add(var)
        if is_common:
            self._commons.add(var)

    # -------------------------------------------------------------
    # Accessors
    # -------------------------------------------------------------
    @property
    def inputs(self) -> set[VarName]:
        return set(self._inputs)

    @property
    def outputs(self) -> set[VarName]:
        return set(self._outputs)

    @property
    def commons(self) -> set[VarName]:
        return set(self._commons)

    # -------------------------------------------------------------
    # Splitting logic
    # -------------------------------------------------------------
    def _parse_var(self, var: VarName) -> tuple[str | None, str | None, str | None, bool]:
        """@brief Re-parse a variable name to obtain (part, rns, unit, is_common)."""
        return self._var_parser(var)

    def build_instrs_dependency_graph(self, insts: list) -> nx.DiGraph:
        """@brief Build a directed dependency graph between instructions based on variable flow.

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
        ext_in = self._inputs | self._commons
        ext_out = self._outputs | self._commons
        ext_vars = self._ext_vars  # local alias

        for idx, inst in enumerate(insts):
            sources = getattr(inst, "src", ()) or ()
            dests = getattr(inst, "dst", ()) or ()

            # Record external vars touched (sources)
            for name, _ in sources:
                if not name:
                    continue
                if name in ext_in:
                    ext_vars.setdefault(idx, set()).add(name)
                writer = last_writer.get(name)
                if writer is not None and writer != idx:
                    if G.has_edge(writer, idx):
                        G[writer][idx].setdefault("vars", set()).add(name)
                    else:
                        G.add_edge(writer, idx, vars={name})

            # Writes (destinations) update last_writer and mark external outputs
            for name, _ in dests:
                if not name:
                    continue
                if name in ext_out:
                    ext_vars.setdefault(idx, set()).add(name)
                last_writer[name] = idx

        return G

    def to_raw_pisa_format(self, parsed_op, name_map: dict[str, str] = None) -> str:
        """@brief Convert a parsed operation back to raw P-ISA format string.

        If name_map is provided, it is used to rename variables accordingly.
        """
        # head
        parts = [str(parsed_op.N), parsed_op.op_name]
        # vars
        for var_name, _ in parsed_op.dst:
            if name_map and var_name in name_map:
                var_name = name_map[var_name]
            parts.append(var_name)
        for var_name, _ in parsed_op.src:
            if name_map and var_name in name_map:
                var_name = name_map[var_name]
            parts.append(var_name)
        # inmediate
        if hasattr(parsed_op, "imm"):
            parts.append(str(parsed_op.imm))
        # tw_meta
        if hasattr(parsed_op, "tw_meta"):
            parts.append(str(parsed_op.tw_meta))
        # stage
        if hasattr(parsed_op, "stage"):
            parts.append(str(parsed_op.stage))
        # block
        if hasattr(parsed_op, "block"):
            parts.append(str(parsed_op.block))
        # res
        if hasattr(parsed_op, "res"):
            parts.append(str(parsed_op.res))
        elif parsed_op.op_name in ("copy", "irshuffle", "rshuffle"):
            parts.append("0")  # these ops require a residual, default to 0
        # comment
        op = ", ".join(parts)
        if hasattr(parsed_op, "comment") and parsed_op.comment:
            op += f"  # {parsed_op.comment}"

        return op

    def write_mem_file(self, file_path: str | Path, instrs: list[DInstruction], externals: set, new_inouts: set = None) -> None:
        """@brief Write a .mem file with given instructions and external variables.

        Args:
            file_path (str | Path): Path to the output .mem file.
            instrs (Iterable): List of instruction objects to write if vars in externals set.
            externals (set): Set of external variable names to include.
            new_inouts (set): Set of new input/output variable names to create new instructions for.
        """
        new_spad_address = 0
        path = Path(file_path)
        with path.open("w", encoding="utf-8") as f:
            for dinstr in instrs:
                if hasattr(dinstr, "var") and dinstr.var in (externals | self.commons):
                    dinstr.address = new_spad_address
                    line = dinstr.to_line()
                    f.write(f"{line}\n")
                    new_spad_address += 1

    def split_mem_info(
        self, mem_path: str | Path, instrs: list[DInstruction], externals: list[set[str]], new_outs: list[dict[str, set[int]]] = None
    ):
        """@brief Split a .mem file into multiple files based on provided external variable sets.

        Args:
            mem_path (str | Path): Path to the original .mem file.
            instrs (List[DInstruction]): List of instruction objects from the original .mem file.
            externals (List[Set[str]]): List of sets of external variable names for each split.
            new_inouts (List[Set[Tuple[int, int, str]]]): Optional list of sets of new input/output variable references for each split.
        """
        print("split mem indo called ROCHA")
        mem_path = Path(mem_path)
        root, ext = mem_path.stem, mem_path.suffix
        long_spad: set[int] = set()
        long_vars: dict[str, tuple[int, set[int]]] = {}
        for idx, ext_vars in enumerate(externals):
            print(f"  Split {idx}: {len(ext_vars)} external variables: {sorted(ext_vars)}")
            output_mem_fname = mem_path.parent / f"{root}_{idx}{ext}"
            with output_mem_fname.open("w", encoding="utf-8") as f:
                new_spad_address = 0
                i = 0
                # Existing DLoads
                while i < len(instrs):
                    dinstr = instrs[i]
                    # Assumes end of load section
                    if isinstance(dinstr, DStore):
                        break
                    if hasattr(dinstr, "var") and dinstr.var in (ext_vars | self.commons):
                        while new_spad_address in long_spad:
                            new_spad_address += 1
                        dinstr.address = new_spad_address
                        line = dinstr.to_line()
                        f.write(f"{line}\n")
                        new_spad_address += 1
                    i += 1

                # Add new inputs if any
                for var, (address, refs) in list(long_vars.items()):
                    if idx in refs:
                        dinstr = DLoad(tokens=[DLoad.name, "poly", address, var], comment="")
                        line = dinstr.to_line()
                        f.write(f"{line}\n")
                        refs.discard(idx)
                        if len(refs) == 0:
                            long_spad.discard(address)
                            long_vars.pop(var, None)

                # Existing DStores
                while i < len(instrs):
                    dinstr = instrs[i]
                    if hasattr(dinstr, "var") and dinstr.var in (ext_vars | self.commons):
                        while new_spad_address in long_spad:
                            new_spad_address += 1
                        dinstr.address = new_spad_address
                        line = dinstr.to_line()
                        f.write(f"{line}\n")
                        new_spad_address += 1
                    i += 1

                # Add new outputs if any
                if new_outs:
                    for var in new_outs[idx]:
                        while new_spad_address in long_spad:
                            new_spad_address += 1
                        long_spad.add(new_spad_address)
                        long_vars[var] = (new_spad_address, new_outs[idx][var])
                        dinstr = DStore(tokens=[DStore.name, var, new_spad_address], comment="")
                        line = dinstr.to_line()
                        f.write(f"{line}\n")
                        new_spad_address += 1

    def get_isolated_instrs_splits(self, graph, insts: list, instr_limit: int, spad_limit: int) -> tuple:
        """
        @brief Propose instruction index splits that fit within given limits.
        """
        # Extract connected components
        components = list(nx.connected_components(graph.to_undirected()))

        print(f"Found {len(components)} isolated components in dependency graph.")
        print(f"Total instructions: {graph.number_of_nodes()}")
        print(f"Common variables: {len(self._commons)}: {sorted(self._commons)}")
        print(f"Total inputs/outputs: {len(self._inputs) + len(self._outputs)}")

        final_splits: list[set[int]] = []
        externals: list[set[str]] = []

        if len(components) > 1:
            t_extrn: set[str] = set()
            p_extrn: set[str] = set()
            t_split: set[int] = set()
            p_split: set[int] = set()

            set_idx: int = 0
            while set_idx < len(components):
                p_split = t_split.copy()
                p_extrn = t_extrn.copy()
                t_split.update(components[set_idx])
                if len(t_split) > instr_limit:
                    t_split.clear()
                    t_extrn.clear()
                    if len(p_split) > 0:
                        final_splits.append(p_split)
                        externals.append(p_extrn)
                    else:
                        break
                else:
                    mem_usage, ext = self._get_external_mem_usage(t_split)
                    t_extrn.update(ext)
                    if mem_usage > spad_limit:
                        t_split.clear()
                        t_extrn.clear()
                        if len(p_split) > 0:
                            final_splits.append(p_split)
                            externals.append(p_extrn)
                        else:
                            break
                    else:
                        set_idx += 1

            if len(t_split) > 0:
                final_splits.append(t_split)
                externals.append(t_extrn)

        # Did all instructions fit in?
        total_instrs = sum(len(s) for s in final_splits) if final_splits else 0
        if total_instrs == graph.number_of_nodes():
            """
            print("\n--- Components Summary ---\n")
            for set_id, instr_set in enumerate(final_splits):
                usage, _ = self._get_external_mem_usage(instr_set)
                print(f"Instruction set {set_id:03d}: \t\tTotal Intructions: {len(instr_set):03d} - Total In/Outs/Commons: {usage}")
                print(f"    Externals: {sorted(externals[set_id])}")
            """
            return final_splits, externals
        else:
            print("Could not fit all instructions into isolated splits; falling back to community-based splitting.")
            return None, None

    def get_community_instrs_splits(self, graph, insts: list, instr_limit: int, spad_limit: int) -> tuple:
        # Extract communities
        communities: list[set[int]] = []
        if graph.number_of_edges() > 0:
            communities = list(nx.community.greedy_modularity_communities(graph.to_undirected()))

        # Delegate community graph build & ordering
        if len(communities) > 0:
            instr_sets, metaG, sorted_communities = self._prepare_community_graph(graph, insts, communities)

        print(f"Found {len(communities)} weakly isolated communities in dependency graph.")
        print(f"Topological sort of communities: {', '.join(map(str, sorted_communities))}")
        """
        print("\n--- Community summary ---\n")
        for set_id in sorted_communities:
            ext_mem_usage, externals = self._get_external_mem_usage(instr_sets[set_id])
            mem_usage, inouts = self._get_inout_mem_usage([set_id], metaG, externals)
            print(
                f"Instruction set {set_id:03d}: \t\tTotal Intructions: {len(instr_sets[set_id]):03d} - "
                f"Total In/Outs/Commons: {mem_usage + ext_mem_usage}"
            )
        """
        final_splits: list[set[int]] = []
        inout_refs: list[dict[str, set[int]]] = []
        final_split_ids: list[set[int]] = []

        t_refs: dict[str, set[int]] = {}
        p_refs: set[tuple[int, int, str]] = set()
        t_split: set[int] = set()
        p_split: set[int] = set()
        t_set_ids: list[int] = []
        p_set_ids: list[int] = []

        idx: int = 0
        while idx < len(sorted_communities):
            p_refs = t_refs.copy()
            p_split = t_split.copy()
            p_set_ids = t_set_ids.copy()
            set_id = sorted_communities[idx]
            t_split.update(instr_sets[set_id])
            t_set_ids.append(set_id)

            if len(t_split) > instr_limit:
                t_refs.clear()
                t_split.clear()
                t_set_ids.clear()
                if len(p_split) > 0:
                    final_splits.append(p_split)
                    final_split_ids.append(set(p_set_ids))
                    inout_refs.append(p_refs)
                else:
                    break
            else:
                ext_mem_usage, externals = self._get_external_mem_usage(t_split)
                inouts_mem_usage, inouts = self._get_inout_mem_usage(t_set_ids, metaG, externals)
                # print(f"ROCHA {set_id} in sets {t_set_ids}")
                # for v in inouts:
                #    print(f"ROCHA {v} out refs {inouts[v]}")
                t_refs = inouts
                if (ext_mem_usage + inouts_mem_usage) > spad_limit:
                    t_refs.clear()
                    t_split.clear()
                    t_set_ids.clear()
                    if len(p_split) > 0:
                        final_splits.append(p_split)
                        final_split_ids.append(set(p_set_ids))
                        inout_refs.append(p_refs)
                    else:
                        break
                else:
                    idx += 1

        if len(t_split) > 0:
            final_splits.append(t_split)
            final_split_ids.append(set(t_set_ids))
            inout_refs.append(t_refs)

        # for new_set_id, ids in enumerate(final_split_ids):
        #    print(f"Final split {new_set_id} contains communities: {sorted(ids)}")

        for new_id, ref in enumerate(inout_refs):
            for v, old_set_ids in ref.items():
                print(f"ROCHA inout var: {v} in sets {new_id} -> {old_set_ids}")
                new_ins: set[int] = set()
                new_set_id = new_id + 1
                while new_set_id < len(final_split_ids):
                    old_ids = final_split_ids[new_set_id]
                    if old_ids & old_set_ids:
                        new_ins.add(new_set_id)
                    new_set_id += 1
                ref[v] = new_ins
                print(f"ROCHA inout var: {v} new sets {new_ins}")

        print(f"ROCHA inout refs: {ref}")

        # Did all instructions fit in?
        externals: list[set[str]] = []
        total_instrs = sum(len(s) for s in final_splits) if final_splits else 0
        if total_instrs == graph.number_of_nodes():
            print("\n--- Final Splits Summary ---\n")
            for set_id, instr_set in enumerate(final_splits):
                ext_mem_usage, exts = self._get_external_mem_usage(instr_set)
                mem_usage, inouts = self._get_inout_mem_usage(final_split_ids[set_id], metaG, exts)
                externals.append(exts)
                print(
                    f"Instruction set {set_id:03d}: \t\tTotal Intructions: {len(instr_set):03d} - "
                    f"Total In/Outs/Commons: {ext_mem_usage} + {mem_usage} = {ext_mem_usage + mem_usage}"
                )

            return final_splits, externals, inout_refs
        else:
            return None, None, None

    def _get_external_mem_usage(
        self,
        instr_set: set[int],
        var_size_map: dict[str, int] | None = None,
    ) -> tuple[int, set[str]]:
        """Return variables tagged as external (inputs/outputs/commons involvement) for the given instruction set."""
        var_size_map = var_size_map or {}
        external_vars: set[str] = set()
        for instr in instr_set:
            ext = self._ext_vars.get(instr)
            if ext:
                external_vars.update(ext)

        total_mem = 0
        for v in external_vars:
            total_mem += int(var_size_map.get(v, 1))
        return total_mem, external_vars

    def _get_inout_mem_usage(
        self,
        set_ids: list[int],
        graph: nx.DiGraph,
        external_vars: set[str],
        var_size_map: dict[str, int] | None = None,
        # ROCHA ) -> Tuple[int, Set[Tuple[int, int, str]]]:
    ) -> tuple[int, dict[str, set[int]]]:
        """Return (inout_vars, inout_refs) crossing instr_set boundary using meta graph edge var_refs."""
        var_size_map = var_size_map or {}
        inouts: set[str] = set()
        # ROCHA inouts_refs: Set[Tuple[int, int, str]] = set()
        outs_refs: dict[str, set[int]] = {}
        for set_id in set_ids:
            # Ins
            for producer, consumer, data in graph.in_edges(set_id, data=True):
                if consumer in set_ids and producer not in set_ids:
                    for _, _, v in data.get("var_refs", set()):
                        if v not in external_vars:
                            # ROCHA inouts_refs.add((p, c, v))
                            inouts.add(v)
            # Outs
            for producer, consumer, data in graph.out_edges(set_id, data=True):
                if producer in set_ids and consumer not in set_ids:
                    for _, _, v in data.get("var_refs", set()):
                        outs_refs.setdefault(v, set()).add(consumer)
                        if v not in external_vars:
                            # ROCHA inouts_refs.add((p, c, v))
                            inouts.add(v)

        vars_used: set[str] = inouts | self._commons
        total_mem = 0
        for v in vars_used:
            total_mem += int(var_size_map.get(v, 1))
        return total_mem, outs_refs
        # ROCHA return total_mem, inouts_refs

    # --- Community graph helpers (refactored to reduce complexity) ---
    def _map_instr_to_community(self, communities: list[set[int]]) -> dict[int, int]:
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
        CG: nx.DiGraph = nx.DiGraph()
        CG.add_nodes_from(range(len(communities)))
        overwritten: dict[int, set[str]] = {}
        for idx in range(base_graph.number_of_nodes()):
            if idx not in instr_to_set:
                continue
            set_id = instr_to_set[idx]
            # Incoming edges
            for prod, cons, data in base_graph.in_edges(idx, data=True):
                p_set = instr_to_set.get(prod)
                if p_set is None or prod in communities[set_id]:
                    continue
                for var in data.get("vars", set()):
                    if var in overwritten.get(set_id, set()):
                        continue
                    if CG.has_edge(p_set, set_id):
                        e = CG[p_set][set_id]
                        e.setdefault("vars", set()).add(var)
                        e.setdefault("var_refs", set()).add((prod, cons, var))
                    else:
                        CG.add_edge(p_set, set_id, vars={var}, var_refs={(prod, cons, var)})
            # Outgoing edges
            for prod, cons, data in base_graph.out_edges(idx, data=True):
                c_set = instr_to_set.get(cons)
                if c_set is None:
                    continue
                if cons in communities[set_id]:
                    for var in data.get("vars", set()):
                        overwritten.setdefault(set_id, set()).add(var)
                    continue
                for var in data.get("vars", set()):
                    if CG.has_edge(set_id, c_set):
                        e = CG[set_id][c_set]
                        e.setdefault("vars", set()).add(var)
                        e.setdefault("var_refs", set()).add((prod, cons, var))
                    else:
                        CG.add_edge(set_id, c_set, vars={var}, var_refs={(prod, cons, var)})
        return CG

    def _condense_community_graph(
        self, comm_graph: nx.DiGraph, communities: list[set[int]]
    ) -> tuple[list[set[int]], nx.DiGraph, list[int]]:
        print("\nCommunity graph contains cycles; condensing strongly connected communities.")
        cond_graph = nx.condensation(comm_graph)
        mapping: dict[int, int] = cond_graph.graph.get("mapping", {})
        # Aggregate attributes
        for u, v, data in comm_graph.edges(data=True):
            cu, cv = mapping[u], mapping[v]
            if cu == cv:
                continue
            vars_set = data.get("vars", set())
            var_refs = data.get("var_refs", set())
            if cond_graph.has_edge(cu, cv):
                cond_graph[cu][cv].setdefault("vars", set()).update(vars_set)
                cond_graph[cu][cv].setdefault("var_refs", set()).update(var_refs)
            else:
                cond_graph.add_edge(cu, cv, vars=set(vars_set), var_refs=set(var_refs))
        # Merge instruction sets per condensed node
        comp_members: dict[int, list[int]] = {}
        for orig, comp_id in mapping.items():
            comp_members.setdefault(comp_id, []).append(orig)
        new_instr_sets: list[set[int]] = []
        for comp_list in comp_members.values():
            merged: set[int] = set()
            for old_sid in comp_list:
                merged.update(communities[old_sid])
            new_instr_sets.append(merged)
        order = list(nx.topological_sort(cond_graph))
        for cid in order:
            print(f"Set_id {cid} condenses communities {sorted(comp_members.get(cid, []))}.")
        return (new_instr_sets if new_instr_sets else communities), cond_graph, order

    def _prepare_community_graph(
        self,
        graph: nx.DiGraph,
        insts: list,  # retained for interface compatibility
        communities: list[set[int]],
    ) -> tuple[list[set[int]], nx.DiGraph, list[int]]:
        """Build community-level dependency graph; condense SCC cycles if present (refactored)."""
        if not communities:
            return [], nx.DiGraph(), []
        instr_to_set = self._map_instr_to_community(communities)
        CG = self._build_community_graph(graph, communities, instr_to_set)
        if nx.is_directed_acyclic_graph(CG):
            order = list(nx.topological_sort(CG))
            return communities, CG, order
        return self._condense_community_graph(CG, communities)

    # --- End community graph helpers ---


__all__ = ["DataSplits"]
