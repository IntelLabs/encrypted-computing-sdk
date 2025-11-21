# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""
@brief Unit tests for kernel_splitter module.
"""

import json
from unittest import mock

import networkx as nx
import pytest
from assembler.common.dinst import DLoad, DStore
from assembler.instructions.xinst import NTT
from assembler.memory_model.variable import Variable
from assembler.stages.prep.kernel_splitter import KernelSplitter


@pytest.fixture
def splitter():
    """Provide a fresh KernelSplitter instance for each test."""
    return KernelSplitter()


@pytest.fixture
def sample_mem_file(tmp_path):
    """Create a sample .mem file for testing."""
    mem_file = tmp_path / "test.mem"
    mem_file.write_text(
        """# Header line 1
# Header line 2
dload, poly, 0, var1
dload, poly, 1, var2
dload, ones, 2, ones_1
dload, ntt_auxiliary_table, 0, ntt_auxiliary_table_0
dload, twid, 4, twid_0
dload, poly, 5, var3
dload, poly, 6, var4
dload, poly, 10, var5
dload, poly, 11, var6
dload, poly, 12, var7
dload, poly, 12, var8
dload, poly, 12, var9
# After 12 vars - these are treated as kernel I/O
dload, poly, 7, input_var
dstore, output_var, 8
dstore, result_var, 9
"""
    )
    return mem_file


class TestKernelSplitterInit:
    """Tests for KernelSplitter initialization."""

    def test_init_creates_empty_collections(self, splitter):
        assert len(splitter.commons) == 0
        assert len(splitter.inputs) == 0
        assert len(splitter.outputs) == 0
        assert len(splitter._ext_vars) == 0


class TestLoadMemFile:
    """Tests for load_mem_file method."""

    def test_load_valid_mem_file(self, splitter, sample_mem_file):
        dinstrs = splitter.load_mem_file(sample_mem_file)
        assert len(dinstrs) > 0
        assert any(isinstance(d, DLoad) for d in dinstrs)
        assert any(isinstance(d, DStore) for d in dinstrs)

    def test_load_nonexistent_file_raises_error(self, splitter):
        with pytest.raises(FileNotFoundError, match=".mem file not found"):
            splitter.load_mem_file("nonexistent.mem")

    def test_load_identifies_commons(self, splitter, sample_mem_file):
        splitter.load_mem_file(sample_mem_file)
        assert "ones_1" in splitter.commons
        assert "ntt_auxiliary_table_0" in splitter.commons
        assert "twid_0" in splitter.commons

    def test_load_identifies_inputs_outputs(self, splitter, sample_mem_file):
        splitter.load_mem_file(sample_mem_file)
        assert "input_var" in splitter.inputs
        assert "output_var" in splitter.outputs
        assert "result_var" in splitter.outputs

    def test_load_invalid_line_raises_error(self, splitter, tmp_path):
        bad_file = tmp_path / "bad.mem"
        bad_file.write_text("invalid line format\n")
        with pytest.raises(RuntimeError, match="No valid instruction found"):
            splitter.load_mem_file(bad_file)


class TestCommonVariableDetection:
    """Tests for common variable identification."""

    def test_is_common_var_detects_common_prefix(self, splitter):
        assert splitter._is_common_var("common_var")
        assert splitter._is_common_var("ntt_table")
        assert splitter._is_common_var("intt_data")
        assert splitter._is_common_var("twid_factor")
        assert splitter._is_common_var("ones_vector")

    def test_is_common_var_rejects_non_common(self, splitter):
        assert not splitter._is_common_var("var1")
        assert not splitter._is_common_var("input_data")
        assert not splitter._is_common_var("")

    def test_register_common_var_adds_to_commons(self, splitter):
        splitter._register_common_var("common_test")
        assert "common_test" in splitter.commons

    def test_register_common_var_ignores_non_common(self, splitter):
        splitter._register_common_var("regular_var")
        assert "regular_var" not in splitter.commons


class TestBuildDependencyGraph:
    """Tests for build_instrs_dependency_graph method."""

    def test_build_empty_graph(self, splitter):
        graph = splitter.build_instrs_dependency_graph([])
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_build_graph_creates_nodes(self, splitter):
        mock_inst1 = mock.Mock(sources=[], dests=[])
        mock_inst2 = mock.Mock(sources=[], dests=[])
        graph = splitter.build_instrs_dependency_graph([mock_inst1, mock_inst2])
        assert graph.number_of_nodes() == 2
        assert 0 in graph.nodes
        assert 1 in graph.nodes

    def test_build_graph_creates_edges_for_dependencies(self, splitter):
        var1 = mock.Mock(name="var1")
        var2 = mock.Mock(name="var2")

        inst1 = mock.Mock(sources=[], dests=[var1])
        inst2 = mock.Mock(sources=[var1], dests=[var2])
        inst3 = mock.Mock(sources=[var2], dests=[])

        graph = splitter.build_instrs_dependency_graph([inst1, inst2, inst3])

        assert graph.has_edge(0, 1)  # inst1 -> inst2
        assert graph.has_edge(1, 2)  # inst2 -> inst3

    def test_build_graph_handles_ntt_special_case(self, splitter):
        # NTT requires actual Variable objects for dest/src
        dest1 = Variable("dest1", 0)
        dest2 = Variable("dest2", 1)
        src1 = Variable("src1", 0)
        src2 = Variable("src2", 1)
        src3 = Variable("src3", 2)
        stage = 0
        res = 1

        ntt1 = NTT(0, 2, [dest1, dest2], [src1, src2, src3], stage, res, 6, 6, "")
        ntt2 = NTT(1, 2, [dest1, dest2], [src1, src2, src3], stage, res, 6, 6, "")

        graph = splitter.build_instrs_dependency_graph([ntt1, ntt2])

        assert graph.has_edge(0, 1)
        assert graph[0][1]["weight"] == 5  # Special weight for NTT chains

    def test_build_graph_tracks_external_vars(self, splitter):
        splitter._inputs.add("input1")
        var = mock.Mock()
        var.name = "input1"  # Set as attribute, not Mock
        inst = mock.Mock(sources=[var], dests=[])

        splitter.build_instrs_dependency_graph([inst])

        assert 0 in splitter._ext_vars
        assert "input1" in splitter._ext_vars[0]


class TestGetExternalMemUsage:
    """Tests for _get_external_mem_usage method."""

    def test_empty_instruction_set_returns_zero(self, splitter):
        mem_usage, ext_vars = splitter._get_external_mem_usage(set())
        assert mem_usage == 0
        assert len(ext_vars) == 0

    def test_calculates_external_var_usage(self, splitter):
        splitter._ext_vars[0] = {"var1", "var2"}
        splitter._ext_vars[1] = {"var2", "var3"}

        mem_usage, ext_vars = splitter._get_external_mem_usage({0, 1})

        assert mem_usage == 3  # var1, var2, var3
        assert ext_vars == {"var1", "var2", "var3"}

    def test_includes_commons_in_calculation(self, splitter):
        splitter._commons = {"common1", "common2"}
        splitter._ext_vars[0] = {"var1"}

        mem_usage, ext_vars = splitter._get_external_mem_usage({0})

        assert mem_usage == 3  # var1 + 2 commons
        assert "common1" not in ext_vars  # Commons not in external vars
        assert "common2" not in ext_vars

    def test_custom_var_size_map(self, splitter):
        splitter._ext_vars[0] = {"large_var"}
        var_size_map = {"large_var": 10}

        mem_usage, _ = splitter._get_external_mem_usage({0}, var_size_map)

        assert mem_usage == 10


class TestGetIsolatedInstrsSplits:
    """Tests for get_isolated_instrs_splits method."""

    def test_empty_graph_returns_empty_splits(self, splitter):
        graph = nx.DiGraph()
        splits, externals = splitter.get_isolated_instrs_splits(graph, 100, 100)
        assert splits == []
        assert externals == []

    def test_single_component_under_limits(self, splitter):
        graph = nx.DiGraph()
        graph.add_nodes_from([0, 1, 2])
        graph.add_edge(0, 1)
        graph.add_edge(1, 2)

        splitter._ext_vars = {0: {"var1"}, 1: {"var2"}, 2: {"var3"}}

        splits, externals = splitter.get_isolated_instrs_splits(graph, 10, 10)

        assert len(splits) == 1
        assert splits[0] == {0, 1, 2}

    def test_multiple_isolated_components(self, splitter):
        graph = nx.DiGraph()
        graph.add_nodes_from([0, 1, 2, 3])
        graph.add_edge(0, 1)  # Component 1
        graph.add_edge(2, 3)  # Component 2

        splitter._ext_vars = {i: {f"var{i}"} for i in range(4)}

        splits, externals = splitter.get_isolated_instrs_splits(graph, 10, 10)

        assert len(splits) >= 1

    def test_exceeds_instruction_limit_returns_none(self, splitter):
        graph = nx.DiGraph()
        graph.add_nodes_from(range(10))
        for i in range(9):
            graph.add_edge(i, i + 1)

        splitter._ext_vars = {i: {f"var{i}"} for i in range(10)}

        splits, externals = splitter.get_isolated_instrs_splits(graph, 5, 100)

        assert splits is None
        assert externals is None


class TestCommunityDetection:
    """Tests for get_community_instrs_splits method."""

    def test_detects_communities_in_graph(self, splitter):
        graph = nx.DiGraph()
        # Create two weakly connected components
        graph.add_edges_from([(0, 1), (1, 2)])
        graph.add_edges_from([(3, 4), (4, 5)])

        splitter._ext_vars = {i: {f"var{i}"} for i in range(6)}

        result = splitter.get_community_instrs_splits(graph, 10, 10)

        assert result is not None
        splits, externals, out_refs = result
        assert len(splits) >= 1


class TestSplitMemInfo:
    """Tests for split_mem_info method."""

    def test_splits_mem_file_into_multiple_files(self, splitter, tmp_path):
        mem_file = tmp_path / "test.mem"
        mem_file.write_text("dload poly 0 var1\ndstore var1 1\n")

        dinstr1 = DLoad(["dload", "poly", "0", "var1"], "")
        dinstr2 = DStore(["dstore", "var1", "1"], "")

        externals = [{"var1"}]

        splitter.split_mem_info(mem_file, [dinstr1, dinstr2], externals)

        expected_file = tmp_path / "test_0.mem"
        assert expected_file.exists()

    def test_writes_dependency_maps(self, splitter, tmp_path):
        mem_file = tmp_path / "test.mem"
        mem_file.write_text("dload poly 0 var1\n")

        dinstr = DLoad(["dload", "poly", "0", "var1"], "")
        externals = [{"var1"}, {"var1"}]

        splitter.split_mem_info(mem_file, [dinstr], externals)

        dep_file = tmp_path / "test_deps_0.json"
        assert dep_file.exists()

        with dep_file.open() as f:
            deps = json.load(f)
            assert isinstance(deps, dict)


class TestRenameVarsInSplits:
    """Tests for rename_vars_in_splits method."""

    def test_renames_boundary_variables(self, splitter):
        var1 = Variable("var1", 1)
        var2 = Variable("var2", 0)

        inst1 = mock.Mock(sources=[], dests=[var1])
        inst2 = mock.Mock(sources=[var1], dests=[var2])

        instr_sets = [{0}, {1}]
        out_refs = [{("var1", 0): {1: {1}}}]

        new_outs = splitter.rename_vars_in_splits([inst1, inst2], instr_sets, out_refs)

        assert len(new_outs) == 1
        # Verify variable was renamed
        renamed_var = inst1.dests[0]
        assert renamed_var.name.startswith("var1_dep_0_0")

    def test_handles_empty_out_refs(self, splitter):
        inst1 = mock.Mock(sources=[], dests=[])
        instr_sets = [{0}]
        out_refs = []

        new_outs = splitter.rename_vars_in_splits([inst1], instr_sets, out_refs)

        assert new_outs == []


class TestPrepareInstructionSplits:
    """Tests for prepare_instruction_splits method."""

    def test_full_splitting_pipeline(self, splitter, sample_mem_file, monkeypatch):
        # Mock args
        args = mock.Mock(
            mem_file=str(sample_mem_file),
            output_file_name="output.pisa",
            split_inst_limit=10,
            split_vars_limit=10,
        )

        # Create mock instructions
        var1 = Variable("var1", 1)
        inst1 = mock.Mock(sources=[], dests=[var1])
        inst1.to_pisa_format = mock.Mock(return_value="inst1")
        inst2 = mock.Mock(sources=[var1], dests=[])
        inst2.to_pisa_format = mock.Mock(return_value="inst2")

        insts_listing = [inst1, inst2]

        # Mock verbose output
        monkeypatch.setattr("assembler.common.config.GlobalConfig.debugVerbose", 0)

        result = splitter.prepare_instruction_splits(args, insts_listing)

        assert isinstance(result, list)
        assert len(result) > 0
        for split_insts, output_path in result:
            assert isinstance(split_insts, list)
            assert isinstance(output_path, str)


class TestCommunityGraphBuilding:
    """Tests for community graph building helpers."""

    def test_map_instr_to_community(self, splitter):
        communities = [{0, 1}, {2, 3}, {4}]
        mapping = splitter._map_instr_to_community(communities)

        assert mapping[0] == 0
        assert mapping[1] == 0
        assert mapping[2] == 1
        assert mapping[3] == 1
        assert mapping[4] == 2

    def test_build_community_graph_creates_edges(self, splitter):
        base_graph = nx.DiGraph()
        # Add all nodes that will be referenced
        base_graph.add_nodes_from([0, 1, 2, 3])
        base_graph.add_edge(0, 2, vars={"shared_var"})

        communities = [{0, 1}, {2, 3}]
        instr_to_set = {0: 0, 1: 0, 2: 1, 3: 1}

        comm_graph = splitter._build_community_graph(base_graph, communities, instr_to_set)

        assert comm_graph.has_edge(0, 1)
        assert "var_refs" in comm_graph[0][1]

    def test_condense_removes_cycles(self, splitter):
        graph = nx.DiGraph()
        graph.add_edges_from([(0, 1), (1, 2), (2, 0)])  # Cycle

        communities = [{0}, {1}, {2}]

        new_sets, condensed = splitter._condense_community_graph(graph, communities)

        assert nx.is_directed_acyclic_graph(condensed)


class TestMergingStrategies:
    """Tests for in-generation and cross-generation merging."""

    def test_rank_pairs_by_common_io(self, splitter):
        graph = nx.DiGraph()
        graph.add_edges_from(
            [
                (10, 0, {"weight": 5}),
                (10, 1, {"weight": 3}),
                (0, 20, {"weight": 2}),
                (1, 20, {"weight": 4}),
            ]
        )

        generation = [0, 1]
        ranked = splitter._rank_generation_pairs_by_common_io(graph, generation)

        assert (0, 1) in ranked
        assert ranked[(0, 1)] > 0  # Should have common pred/succ

    def test_rebuild_generation_pairs_after_merge(self, splitter):
        cluster_sets = {0: {0, 1}, 2: {2, 3}}
        ranked_pairs = {(0, 2): 5.0, (1, 2): 3.0, (0, 3): 2.0}

        rebuilt = splitter._rebuild_generation_pairs(cluster_sets, ranked_pairs)

        assert (0, 2) in rebuilt
        # Score should aggregate individual member scores
        assert rebuilt[(0, 2)] == 5.0 + 3.0 + 2.0


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_handles_instructions_without_sources_or_dests(self, splitter):
        inst = mock.Mock(sources=[], dests=[])
        graph = splitter.build_instrs_dependency_graph([inst])
        assert graph.number_of_nodes() == 1

    def test_handles_variables_without_names(self, splitter):
        var_no_name = mock.Mock(name=None)
        inst = mock.Mock(sources=[var_no_name], dests=[])
        graph = splitter.build_instrs_dependency_graph([inst])
        assert graph.number_of_edges() == 0

    def test_split_with_no_available_splits_raises_error(self, splitter, sample_mem_file):
        args = mock.Mock(
            mem_file=str(sample_mem_file),
            output_file_name="output.pisa",
            split_inst_limit=1,  # Impossible limit
            split_vars_limit=1,
        )

        var1 = Variable("var1", 0)
        inst1 = mock.Mock(sources=[], dests=[var1])
        inst2 = mock.Mock(sources=[var1], dests=[])

        with pytest.raises(RuntimeError, match="Final instruction splits do not cover all instructions."):
            splitter.prepare_instruction_splits(args, [inst1, inst2])
