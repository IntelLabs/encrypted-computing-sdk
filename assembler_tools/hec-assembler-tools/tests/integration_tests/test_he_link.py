# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link.py
@brief Integration tests for the he_link module
"""

import shutil
import tempfile
from pathlib import Path

import he_link
import pytest
from linker.kern_trace.trace_info import TraceInfo
from linker.linker_run_config import LinkerRunConfig


class TestHeIntegration:
    """
    @class TestHeIntegration
    @brief Integration tests for the he_link module
    """

    @pytest.fixture
    def temp_dir(self):
        """
        @brief Create a temporary directory for test files
        """
        tmp_dir = tempfile.mkdtemp()
        yield tmp_dir
        shutil.rmtree(tmp_dir)

    @pytest.mark.parametrize(
        "fixture_dir,input_prefix",
        [
            ("bgv_multi_add_add_mul_8192_l1_m2", "bgv_add_8192_l1_m2_pisa.tw"),
            ("bgv_multi_mul_relin_16384_l1_m2", "bgv_relin_16384_l1_m2_pisa.tw"),
        ],
    )
    def test_run_he_link_on_single_op_hbm(self, temp_dir, fixture_dir, input_prefix):
        """
        @brief Test he_link.py with .cinst/.minst/.xinst input files from linking_fixtures
        """
        fixtures_root = Path(__file__).parent / "linking_fixtures" / fixture_dir / "hbm"
        input_files = {
            "minst": fixtures_root / f"{input_prefix}.minst",
            "cinst": fixtures_root / f"{input_prefix}.cinst",
            "xinst": fixtures_root / f"{input_prefix}.xinst",
            "mem": fixtures_root / f"{input_prefix}.mem",
        }

        # Copy to temp input dir
        input_dir = Path(temp_dir) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        for input_file in input_files.values():
            shutil.copy(input_file, input_dir)

        # Prepare config
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        # No mem file for this minimal test
        cfg_kwargs = {
            "input_prefixes": [input_prefix],
            "output_prefix": "linked_output",
            "input_mem_file": input_files["mem"],
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "using_trace_file": False,
            "use_xinstfetch": False,
            "has_hbm": True,
            "hbm_size": 2048,
        }

        # Run he_link
        he_link.main(LinkerRunConfig(**cfg_kwargs))

        # Check output .cinst, .minst, .xinst files exist and have same number of lines as input
        for ext in [".cinst", ".minst", ".xinst"]:
            out_file = output_dir / f"{cfg_kwargs['output_prefix']}{ext}"
            in_file = input_dir / f"{input_prefix}{ext}"
            assert out_file.exists()
            assert in_file.exists()
            with open(out_file, encoding="utf-8") as fout, open(in_file, encoding="utf-8") as fin:
                assert sum(1 for _ in fout) == sum(1 for _ in fin)

    @pytest.mark.parametrize(
        "fixture_dir,input_prefix",
        [
            ("bgv_multi_add_add_mul_8192_l1_m2", "bgv_add_8192_l1_m2_pisa.tw"),
            ("bgv_multi_mul_relin_16384_l1_m2", "bgv_relin_16384_l1_m2_pisa.tw"),
        ],
    )
    def test_run_he_link_on_single_op_no_hbm(self, temp_dir, fixture_dir, input_prefix):
        """
        @brief Test he_link.py with .cinst/.minst/.xinst input files from linking_fixtures
        """
        fixtures_root = Path(__file__).parent / "linking_fixtures" / fixture_dir / "no_hbm"
        input_files = {
            "minst": fixtures_root / f"{input_prefix}.minst",
            "cinst": fixtures_root / f"{input_prefix}.cinst",
            "xinst": fixtures_root / f"{input_prefix}.xinst",
            "mem": fixtures_root / f"{input_prefix}.mem",
        }

        # Copy to temp input dir
        input_dir = Path(temp_dir) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        for input_file in input_files.values():
            shutil.copy(input_file, input_dir)

        # Prepare config
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        # No mem file for this minimal test
        cfg_kwargs = {
            "input_prefixes": [input_prefix],
            "output_prefix": "linked_output",
            "input_mem_file": input_files["mem"],
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "using_trace_file": False,
            "use_xinstfetch": False,
            "has_hbm": False,
            "hbm_size": 2048,
        }

        # Run he_link
        he_link.main(LinkerRunConfig(**cfg_kwargs))

        # Check output .xinst files exist and have same number of lines as input
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.xinst"
        assert out_file.exists()
        assert input_files["xinst"].exists()
        with open(out_file, encoding="utf-8") as fout, open(input_files["xinst"], encoding="utf-8") as fin:
            assert sum(1 for _ in fout) == sum(1 for _ in fin)

        # Assert no csyncm instructions in cinst output file
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.cinst"
        assert out_file.exists()
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
            assert "csyncm" not in content, "Found csyncm instruction in cinst output file"

        # Assert minst is one line
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.minst"
        assert out_file.exists()
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
            assert content.count("\n") == 1, "Expected minst output to be a single line"

    def _extract_trace_vars(self, kernel_ops):
        """
        Helper to extract input, output, and intermediate variables from kernel_ops.
        """
        input_vars = set()
        output_vars = set()
        for op in kernel_ops:
            op_vars = op.kern_vars
            output_vars.add(op_vars[0].label)
            for var in op_vars[1:]:
                input_vars.add(var.label)
        overall_input_vars = input_vars - output_vars
        overall_output_vars = output_vars - input_vars
        intermediate_vars = input_vars & output_vars
        return overall_input_vars, overall_output_vars, intermediate_vars

    def _parse_n_test_mem_file(self, mem_file):
        """
        Helper to parse mem file and return dload/dstore vars and labels.
        Also checks address uniqueness/consecutiveness and duplicates.
        """
        assert mem_file.exists()

        with open(mem_file, encoding="utf-8") as f:
            split_lines = f.read().splitlines()
        dload_vars, dload_var_labels = [], set()
        dstore_vars, dstore_var_labels = [], set()
        for idx, line in enumerate(split_lines):
            tokens = line.split(",")
            if tokens[0].startswith("dload"):
                var_name = tokens[3].strip()
                dload_vars.append(var_name)
                if var_name.startswith("ct") or var_name.startswith("pt"):
                    dload_var_labels.add(var_name.split("_")[0])
            if tokens[0].startswith("dstore"):
                var_name = tokens[1].strip()
                dstore_vars.append(var_name)
                if var_name.startswith("ct") or var_name.startswith("pt"):
                    dstore_var_labels.add(var_name.split("_")[0])

            # Assert addresses are digits
            assert tokens[2].strip().isdigit(), f"Expected address {tokens[2]} to be digit in line: {line}"
            # Assert addresses are unique and consecutive
            assert idx == int(tokens[2]), f"Expected address {idx + 1} but found {tokens[2]} in line: {line}"

        # Assert no duplicates in dload/dstore vars
        assert len(dload_vars) == len(set(dload_vars)), "Found duplicate dload variables in mem file"
        assert len(dstore_vars) == len(set(dstore_vars)), "Found duplicate dstore variables in mem file"

        return dload_var_labels, dstore_var_labels

    def _get_mem_hbm_addresses(self, mem_file):
        """
        Helper to extract mload and mstore addresses from mem file.
        """
        assert mem_file.exists()

        with open(mem_file, encoding="utf-8") as f:
            split_lines = f.read().splitlines()
        dload_addresses, dstore_addresses = set(), set()
        for line in split_lines:
            instr, _ = line.split("#", 1) if "#" in line else (line, "")
            if line.startswith("dload"):
                dload_addresses.add(instr.split(",")[2].strip())
            elif line.startswith("dstore"):
                dstore_addresses.add(instr.split(",")[2].strip())

        return dload_addresses, dstore_addresses

    def _get_minst_spad_addresses(self, minstrs):
        """
        @brief Helper to extract mload and mstore addresses from minst instructions.

        @param minstrs List of MInstructions as lists of tokens.
        @return tuple (mload_addresses, mstore_addresses) Sets of addresses.
        """
        mload_addresses, mstore_addresses = set(), set()
        for minst in minstrs:
            if minst[1].startswith("mload"):
                mload_addresses.add(minst[2])
            elif minst[1].startswith("mstore"):
                mstore_addresses.add(minst[3])
        return mload_addresses, mstore_addresses

    def _parse_cinst_file(self, cinst_file):
        """
        @brief Helper to parse cinst file and return a list of CInstructions.

        @param cinst_file Path to the cinst file.
        @return List of CInstructions as lists of tokens.
        """
        assert cinst_file.exists()

        # Save tokenized cinsts
        with open(cinst_file, encoding="utf-8") as f:
            lines = f.read().splitlines()

        cinstrs: list[list] = []
        for line in lines:
            instr, _ = line.split("#", 1) if "#" in line else (line, "")
            tokens = [token.strip() for token in instr.split(",")]
            cinstrs.append(tokens)

        return cinstrs

    def _parse_minst_file(self, minst_file):
        """
        @brief Helper to parse minst file and return a list of MInstructions.

        @param minst_file Path to the minst file.
        @return List of MInstructions as lists of tokens.
        """
        assert minst_file.exists()
        # Save tokenized minst instructions
        with open(minst_file, encoding="utf-8") as f:
            lines = f.read().splitlines()

        minstrs: list[list] = []
        for line in lines:
            instr, _ = line.split("#", 1) if "#" in line else (line, "")
            tokens = [token.strip() for token in instr.split(",")]
            minstrs.append(tokens)

        return minstrs

    def _parse_xinst_file(self, xinst_file):
        """
        @brief Helper to parse xinst file and return a list of XInstructions.

        @param xinst_file Path to the xinst file.
        @return List of XInstructions as lists of tokens.
        """
        assert xinst_file.exists()
        # Save tokenized xinst instructions
        with open(xinst_file, encoding="utf-8") as f:
            lines = f.read().splitlines()
        xinstrs: list[list] = []
        for line in lines:
            instr, _ = line.split("#", 1) if "#" in line else (line, "")
            tokens = [token.strip() for token in instr.split(",")]
            xinstrs.append(tokens)
        return xinstrs

    def run_he_link_with_trace_file(self, temp_dir, fixture_dir, hbm_enabled, keep_hbm_boundary, keep_spad_boundary):
        """
        @brief Helper to run he_link with trace file input

        @param temp_dir Temporary directory for input/output files
        @param fixture_dir Directory containing fixture files
        @param hbm_enabled Whether to enable HBM
        @param keep_hbm_boundary Whether to keep HBM boundary
        @param keep_spad_boundary Whether to keep SPAD boundary

        @return tuple containing (output_dir, output_prefix, kernel_ops)
        """
        fixtures_root = Path(__file__).parent / "linking_fixtures" / fixture_dir
        trace_file_name = f"{fixture_dir}_program_trace.csv"
        cfg_kwargs = {
            "input_prefixes": [],
            "output_prefix": "linked_output_trace",
            "input_mem_file": None,
            "input_dir": str(Path(temp_dir) / "input"),
            "output_dir": str(Path(temp_dir) / "output"),
            "trace_file": str(Path(temp_dir) / "input" / trace_file_name),
            "using_trace_file": True,
            "use_xinstfetch": False,
            "keep_hbm_boundary": keep_hbm_boundary,
            "keep_spad_boundary": keep_spad_boundary,
            "has_hbm": hbm_enabled,
            "hbm_size": 2048,
        }

        # Copy to temp input dir
        Path(cfg_kwargs["input_dir"]).mkdir(parents=True, exist_ok=True)
        shutil.copy(fixtures_root / trace_file_name, cfg_kwargs["input_dir"])

        # Copy hbm or no_hbm folder content to input_dir
        content_dir = fixtures_root / ("hbm" if hbm_enabled else "no_hbm")
        for item in content_dir.iterdir():
            if item.is_file():
                shutil.copy(item, cfg_kwargs["input_dir"])

        # Prepare config
        Path(cfg_kwargs["output_dir"]).mkdir(exist_ok=True)

        # Run he_link
        he_link.main(LinkerRunConfig(**cfg_kwargs))

        # Check all output files exist
        output_dir = Path(cfg_kwargs["output_dir"])
        output_prefix = cfg_kwargs["output_prefix"]
        for ext in [".xinst", ".minst", ".cinst", ".mem"]:
            out_file = output_dir / f"{output_prefix}{ext}"
            assert out_file.exists(), f"Output file {out_file} does not exist"

        # Extract trace vars for tests
        kernel_ops = TraceInfo.parse_kernel_ops_from_file(cfg_kwargs["trace_file"])

        # Return needed information for tests
        return (output_dir, output_prefix, kernel_ops)

    @pytest.fixture
    def run_he_link_trace_hbm_no_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM enabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=True, keep_hbm_boundary=False, keep_spad_boundary=False)

    @pytest.fixture
    def run_he_link_trace_hbm_spad_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM enabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=True, keep_hbm_boundary=False, keep_spad_boundary=True)

    @pytest.fixture
    def run_he_link_trace_hbm_with_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM enabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=True, keep_hbm_boundary=True, keep_spad_boundary=True)

    @pytest.fixture
    def run_he_link_trace_no_hbm_no_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM disabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=False, keep_hbm_boundary=False, keep_spad_boundary=False)

    @pytest.fixture
    def run_he_link_trace_no_hbm_spad_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM disabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=False, keep_hbm_boundary=False, keep_spad_boundary=True)

    @pytest.fixture
    def run_he_link_trace_no_hbm_with_boundary(self, temp_dir, fixture_dir):
        """
        @brief Fixture to run he_link once with trace file input and HBM disabled

        @return tuple containing (output_dir, output_prefix, trace_file, kernel_ops)
        """
        return self.run_he_link_with_trace_file(temp_dir, fixture_dir, hbm_enabled=False, keep_hbm_boundary=True, keep_spad_boundary=True)

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    @pytest.mark.parametrize("run_fixture", ["run_he_link_trace_hbm_no_boundary", "run_he_link_trace_no_hbm_no_boundary"])
    def test_mem_output_trace_file(self, fixture_dir, run_fixture, request):
        """
        @brief Test he_link.py with a trace file input from linking_fixtures
        """
        # Get the fixture function by name and call it
        run_func = request.getfixturevalue(run_fixture)
        output_dir, output_prefix, kernel_ops = run_func

        # Extract trace vars
        overall_input_vars, overall_output_vars, intermediate_vars = self._extract_trace_vars(kernel_ops)

        # Check output *.mem
        dload_var_labels, dstore_var_labels = self._parse_n_test_mem_file(output_dir / f"{output_prefix}.mem")

        # Assert dload and dstore vars match overall input/output trace vars
        assert dload_var_labels == overall_input_vars
        assert dstore_var_labels == overall_output_vars

        # Assert no intermediate variables in *.mem file
        assert not dload_var_labels.intersection(intermediate_vars), (
            "Found intermediate variables in dload_var_labels: " f"{dload_var_labels.intersection(intermediate_vars)}"
        )
        assert not dstore_var_labels.intersection(intermediate_vars), (
            "Found intermediate variables in dstore_var_labels: " f"{dstore_var_labels.intersection(intermediate_vars)}"
        )

    def _validate_minst_file_common(self, output_dir, output_prefix):
        """
        Helper to validate common aspects of minst files in both boundary and no-boundary tests.
        Returns parsed data for additional specific validations.
        """
        # .mem info
        dload_addresses, dstore_addresses = self._get_mem_hbm_addresses(output_dir / f"{output_prefix}.mem")

        # .cinst info
        cinstrs = self._parse_cinst_file(output_dir / f"{output_prefix}.cinst")

        # Check output .minst file
        minst_file = output_dir / f"{output_prefix}.minst"

        # Read minst file content
        minstrs = self._parse_minst_file(minst_file)

        # Assert minst file has content (should contain MInstructions)
        assert len(minstrs) > 0, "Expected minst file to have content"

        # Assert last line contains msyncc (termination instruction)
        last_tokens = minstrs[-1]
        assert "msyncc" in last_tokens[1], "Expected last line to contain msyncc termination instruction"

        last_cinst_spad = 0
        spad_address_resets = 0
        for i, tokens in enumerate(minstrs[:-1]):
            # Assert no empty lines in between (except possibly the last one)
            assert tokens, f"Found empty line at index {i} in minst file"
            # Assert index is consecutive
            assert int(tokens[0]) == i, f"Expected index {i} but found {tokens[0]} in line: {", ".join(tokens)}"
            # Assert mload/mstore addresses are digits
            if tokens[1].startswith("mstore") or tokens[1].startswith("mload"):
                assert tokens[2].isdigit(), f"Expected address {tokens[2]} to be digit in line: {", ".join(tokens)}"
                assert tokens[3].isdigit(), f"Expected address {tokens[3]} to be digit in line: {", ".join(tokens)}"

                if tokens[1].startswith("mload") and tokens[3] == "0":
                    # If mload address is 0, it should be a reset
                    spad_address_resets += 1

                elif tokens[1].startswith("mstore"):
                    # Assert previous instruction was an msyncc
                    assert minstrs[i - 1][1].startswith(
                        "msyncc"
                    ), f"Expected mstore to follow msyncc in line: {", ".join(tokens)} - prev: {", ".join(minstrs[i - 1])}"
                    # Assert mstore's SPAD address is its cstore's SPAD address
                    assert tokens[3] == last_cinst_spad, (
                        f"Expected mstore SPAD address {tokens[3]} to match last cstore SPAD address "
                        f"{last_cinst_spad} in line: {", ".join(tokens)}"
                    )

            elif tokens[1].startswith("msyncc"):
                target = tokens[2].strip()
                # Assert msyncc targets are digits
                assert target.isdigit(), f"Expected msyncc target to be digit in line: {", ".join(tokens)}"
                # Assert targeted cinst is a cstore
                assert cinstrs[int(target)][1].startswith(
                    "cstore"
                ), f"Expected msyncc target {target} to be a cstore in line: {", ".join(tokens)}"
                last_cinst_spad = cinstrs[int(target)][2].strip()

        return {
            "minstrs": minstrs,
            "cinstrs": cinstrs,
            "dload_addresses": dload_addresses,
            "dstore_addresses": dstore_addresses,
            "spad_address_resets": spad_address_resets,
        }

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_minst_output_trace_file_hbm_no_boundary(self, run_he_link_trace_hbm_no_boundary):
        """
        @brief Test .minst file output from he_link.py with trace file input and HBM enabled
        """
        output_dir, output_prefix, _ = run_he_link_trace_hbm_no_boundary

        # Validate common aspects and get validation data
        validation_data = self._validate_minst_file_common(output_dir, output_prefix)

        minstrs = validation_data["minstrs"]
        dload_addresses = validation_data["dload_addresses"]
        dstore_addresses = validation_data["dstore_addresses"]
        spad_address_resets = validation_data["spad_address_resets"]
        mload_spad_addresses = set()

        # No-boundary specific validations:
        # Check each instruction's addresses are in expected sets
        for tokens in minstrs[:-1]:
            if tokens[1].startswith("mload"):
                # Assert mload's hbm addresses are in expected set
                assert (
                    tokens[3] in dload_addresses
                ), f"Expected mload HBM address {tokens[3]} to be in {dload_addresses} in line: {", ".join(tokens)}"
                # Assert spad address is not duplicate in mload sequence
                assert (
                    tokens[2] not in mload_spad_addresses
                ), f"Expected mload SPAD address {tokens[2]} to be unique within mload sequence for line: {", ".join(tokens)}"
                mload_spad_addresses.add(tokens[2])
            elif tokens[1].startswith("mstore"):
                # Assert mstore's hbm addresses are in expected set
                assert (
                    tokens[2] in dstore_addresses
                ), f"Expected mstore HBM address {tokens[2]} to be in {dstore_addresses} in line: {", ".join(tokens)}"

        # Assert spad resets count matches 1
        assert spad_address_resets == 1, f"Expected 1 spad resets but found {spad_address_resets} in minst file"

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_minst_output_trace_file_hbm_with_boundary(self, run_he_link_trace_hbm_with_boundary):
        """
        @brief Test .minst file output from he_link.py with trace file input and HBM enabled
        """
        output_dir, output_prefix, kernel_ops = run_he_link_trace_hbm_with_boundary

        # Validate common aspects and get validation data
        validation_data = self._validate_minst_file_common(output_dir, output_prefix)

        minstrs = validation_data["minstrs"]
        dload_addresses = validation_data["dload_addresses"]
        spad_address_resets = validation_data["spad_address_resets"]
        mload_spad_addresses = set()
        mstore_hbm_addresses = set()

        # With-boundary specific validations:
        # We need to track HBM addresses across the file
        for tokens in minstrs[:-1]:
            if tokens[1].startswith("mload"):
                # Assert mload's hbm addresses are in expected set
                assert tokens[3] in (
                    dload_addresses | mstore_hbm_addresses
                ), f"Expected mload HBM address {tokens[3]} to be in {dload_addresses | mstore_hbm_addresses} in line: {", ".join(tokens)}"
                # Reset tracking for each new kernel
                if tokens[3] == "0":
                    mload_spad_addresses = set()

                # Assert spad address is not duplicate in mload sequence
                assert (
                    tokens[2] not in mload_spad_addresses
                ), f"Expected mload SPAD address {tokens[2]} to be unique within mload sequence for line: {", ".join(tokens)}"
                mload_spad_addresses.add(tokens[2])
            elif tokens[1].startswith("mstore"):
                # Track intermediate mstore addresses for later mloads
                if tokens[2] not in dload_addresses:
                    mstore_hbm_addresses.add(tokens[2])

        # Assert spad resets count matches expected kernel ops
        assert spad_address_resets == len(
            kernel_ops
        ), f"Expected {len(kernel_ops)} spad resets but found {spad_address_resets} in minst file"

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    @pytest.mark.parametrize("run_fixture", ["run_he_link_trace_no_hbm_no_boundary", "run_he_link_trace_no_hbm_with_boundary"])
    def test_minst_output_trace_file_no_hbm(self, fixture_dir, run_fixture, request):
        """
        @brief Test he_link.py with a trace file input from linking_fixtures
        """
        # Get the fixture function by name and call it
        run_func = request.getfixturevalue(run_fixture)
        output_dir, output_prefix, _ = run_func

        # Assert minst is one line
        out_file = output_dir / f"{output_prefix}.minst"
        assert out_file.exists()
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
            assert content.count("\n") == 1, "Expected minst output to be a single line"

    def _validate_cinst_file_hbm_common(self, output_dir, output_prefix):
        """
        @brief Common validation logic for cinst files with HBM enabled

        @param output_dir Path to output directory
        @param output_prefix Prefix for output files
        @param kernel_ops List of kernel operations (optional)
        @param check_kernel_count Whether to validate kernel count against kernel_ops
        @return Dictionary of validation counts and data for specific test assertions
        """
        # Get instructions from cinst/minst files
        cinstrs = self._parse_cinst_file(output_dir / f"{output_prefix}.cinst")
        minstrs = self._parse_minst_file(output_dir / f"{output_prefix}.minst")
        xinstrs = self._parse_xinst_file(output_dir / f"{output_prefix}.xinst")

        mload_addresses, mstore_addresses = self._get_minst_spad_addresses(minstrs)
        last_bundle = int(xinstrs[-1][0][1:])  # Remove 'F' prefix from last bundle

        # Assert cinst file has content (should contain CInstructions)
        assert len(cinstrs) > 0, "Expected cinst file to have content"

        # Validation data
        last_minstr_spad = 0
        cstore_spad_addresses = set()
        csyncm_count = 0

        # Validate cinst file content
        for i, tokens in enumerate(cinstrs[:-1]):
            if tokens[1].startswith("csyncm"):
                csyncm_count += 1
                # Assert csyncm targets are digits
                assert tokens[2].isdigit(), f"Expected csyncm target to be digit in line: {", ".join(tokens)}"
                # Not second last instruction
                if i < len(cinstrs) - 2:
                    target_minst = minstrs[int(tokens[2])]
                    last_minstr_spad = target_minst[2]

            elif tokens[1] in ["cload", "bload", "nload", "bones"]:
                # Assert cload/bload/nload/bones SPAD address is digits
                assert tokens[3].isdigit(), f"Expected SPAD address {tokens[3]} to be digit in line: {", ".join(tokens)}"
                # Assert SPAD address is in mload_addresses or cstore_spad_addresses
                assert tokens[3] in (mload_addresses | cstore_spad_addresses), (
                    f"Expected SPAD address {tokens[3]} to be in mload or mstore addresses "
                    f"in line: {", ".join(tokens)}  cstore addresses: {cstore_spad_addresses}"
                )
                if tokens[1] in ["cload", "bload"] and tokens[3] in mload_addresses:
                    # Assert cload/bload SPAD address is last mload's SPAD address
                    assert tokens[3] == last_minstr_spad, (
                        f"Expected SPAD address {tokens[3]} to match last mload's SPAD "
                        f"address {last_minstr_spad} in line: {", ".join(tokens)}"
                    )

                if tokens[1].startswith("bones") and tokens[2] in mload_addresses:
                    # Assert bones SPAD address is last mload's SPAD address
                    assert tokens[2] == last_minstr_spad, (
                        f"Expected SPAD address {tokens[2]} to match last mload's SPAD "
                        f"address {last_minstr_spad} in line: {", ".join(tokens)}"
                    )

            elif tokens[1].startswith("cstore"):
                # Assert cstore SPAD address is digits
                assert tokens[2].isdigit(), f"Expected SPAD address {tokens[2]} to be digit in line: {", ".join(tokens)}"
                if tokens[2] not in mstore_addresses:
                    cstore_spad_addresses.add(tokens[2])

            elif tokens[1].startswith("ifetch"):
                # Assert ifetch target is digits
                assert tokens[2].isdigit(), f"Expected ifetch target {tokens[2]} to be digit in line: {", ".join(tokens)}"
                # Assert ifetch target is a valid xinst bundle
                assert (
                    int(tokens[2]) <= last_bundle
                ), f"Expected ifetch target {tokens[2]} to be less than or equal to last bundle {last_bundle} in line: {", ".join(tokens)}"

            # Assert no empty lines in between (except possibly the last one)
            assert tokens, "Found empty line in cinst file"

            # Assert index is consecutive
            assert int(tokens[0]) == i, f"Expected index {i} but found {tokens[0]} in line: {", ".join(tokens)}"

        # Assert last line contains cexit (termination instruction)
        last_tokens = cinstrs[-1]
        assert "cexit" in last_tokens[1], "Expected last line to contain cexit termination instruction"

        # Assert last csyncm (second last instruction) is present
        csyncm_tokens = cinstrs[-2]
        assert csyncm_tokens[1].startswith("csyncm"), "Expected second last line to contain csyncm instruction"
        # Assert last csyncm's target is digits
        assert csyncm_tokens[2].isdigit(), f"Expected last csyncm target {csyncm_tokens[2]} to be digit in line: {", ".join(csyncm_tokens)}"
        # Assert last csyncm's target is the second last minst
        assert int(csyncm_tokens[2]) == len(minstrs) - 2, "Expected last csyncm target to be the second last minst"
        # Assert csyncm instructions are present in HBM mode (they should be kept)
        assert csyncm_count > 0, "Expected to find csyncm instructions in cinst output file for HBM mode"

        # Return validation data for any additional test-specific assertions
        return {"csyncm_count": csyncm_count, "cinstrs": cinstrs, "minstrs": minstrs}

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_cinst_output_trace_file_hbm_no_boundary(self, run_he_link_trace_hbm_no_boundary):
        """
        @brief Test .cinst file output from he_link.py with trace file input and HBM enabled
        """
        output_dir, output_prefix, _ = run_he_link_trace_hbm_no_boundary

        # Validate common aspects and get validation data
        validation_data = self._validate_cinst_file_hbm_common(output_dir, output_prefix)

        # Get instructions from cinst/minst files
        cinstrs = validation_data["cinstrs"]
        minstrs = validation_data["minstrs"]

        # Validate specific cinst file content
        for i, tokens in enumerate(cinstrs[:-1]):
            if tokens[1].startswith("csyncm"):
                # Not second last instruction
                if i < len(cinstrs) - 2:
                    # Assert targeted minst is an mload
                    assert minstrs[int(tokens[2])][1].startswith(
                        "mload"
                    ), f"Expected csyncm target {tokens[2]} to be a mload in line: {", ".join(tokens)}"

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_cinst_output_trace_file_hbm_spad_boundary(self, run_he_link_trace_hbm_spad_boundary):
        """
        @brief Test .cinst file output from he_link.py with trace file input and HBM enabled
        """
        output_dir, output_prefix, _ = run_he_link_trace_hbm_spad_boundary

        # Validate common aspects and get validation data
        validation_data = self._validate_cinst_file_hbm_common(output_dir, output_prefix)

        # Get instructions from cinst/minst files
        cinstrs = validation_data["cinstrs"]
        minstrs = validation_data["minstrs"]

        # Validate specific cinst file content
        for i, tokens in enumerate(cinstrs[:-1]):
            if tokens[1].startswith("csyncm"):
                # Not second last instruction
                if i < len(cinstrs) - 2:
                    # Assert targeted minst is an mload
                    assert minstrs[int(tokens[2])][1].startswith(
                        "mload"
                    ), f"Expected csyncm target {tokens[2]} to be a mload in line: {", ".join(tokens)}"

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_cinst_output_trace_file_hbm_with_boundary(self, run_he_link_trace_hbm_with_boundary):
        """
        @brief Test .cinst file output from he_link.py with trace file input and HBM enabled
        """
        output_dir, output_prefix, kernel_ops = run_he_link_trace_hbm_with_boundary

        # Validate common aspects and get validation data
        validation_data = self._validate_cinst_file_hbm_common(output_dir, output_prefix)

        # Get instructions from cinst/minst files
        cinstrs = validation_data["cinstrs"]
        minstrs = validation_data["minstrs"]

        # Validate specific cinst file content
        kernels_count = 0
        for tokens in cinstrs[:-1]:
            if tokens[1].startswith("csyncm"):
                # Assert targeted minst is an mload/mstore
                assert minstrs[int(tokens[2])][1] in (
                    "mload",
                    "mstore",
                ), f"Expected csyncm target {tokens[2]} to be a mload in line: {", ".join(tokens)}"

            elif tokens[1].startswith("cload"):
                if tokens[3] == "13":
                    # If cload/bload SPAD address is 13, it should be a new kernel operation
                    kernels_count += 1

        # Assert kernels count matches expected
        assert kernels_count == len(kernel_ops), f"Expected {len(kernel_ops)} kernels but found {kernels_count} in cinst file"

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    @pytest.mark.parametrize(
        "run_fixture",
        ["run_he_link_trace_no_hbm_spad_boundary", "run_he_link_trace_no_hbm_with_boundary", "run_he_link_trace_no_hbm_no_boundary"],
    )
    def test_cinst_output_trace_file_no_hbm(self, fixture_dir, run_fixture, request):
        """
        @brief Test .cinst file output from he_link.py with trace file input and no HBM
        """
        # Get the fixture function by name and call it
        run_func = request.getfixturevalue(run_fixture)
        output_dir, output_prefix, _ = run_func

        # .mem info
        dload_addresses, _ = self._get_mem_hbm_addresses(output_dir / f"{output_prefix}.mem")

        # Read cinst/xinst file content
        cinstrs = self._parse_cinst_file(output_dir / f"{output_prefix}.cinst")
        xinstrs = self._parse_xinst_file(output_dir / f"{output_prefix}.xinst")

        last_bundle = int(xinstrs[-1][0][1:])  # Remove 'F' prefix from last bundle

        # Assert cinst file has content (should contain CInstructions)
        assert len(cinstrs) > 0, "Expected cinst file to have content"

        cstore_spad_addresses = set()

        # Check each instruction's addresses are in expected sets
        for i, tokens in enumerate(cinstrs[:-1]):
            # Assert no empty lines in between (except possibly the last one)
            assert tokens, f"Found empty line at index {i} in minst file"
            # Assert index is consecutive
            assert int(tokens[0]) == i, f"Expected index {i} but found {tokens[0]} in line: {", ".join(tokens)}"

            if tokens[1].startswith("cstore"):
                # Assert cstore's spad addresses are digits
                assert tokens[2].isdigit(), f"Expected address {tokens[2]} to be digit in line: {", ".join(tokens)}"
                cstore_spad_addresses.add(tokens[2])
            elif tokens[1].startswith("cload"):
                # Assert cload's spad addresses are digits
                assert tokens[3].isdigit(), f"Expected address {tokens[3]} to be digit in line: {", ".join(tokens)}"
                # Assert cload's spad addresses are in expected set
                assert tokens[3] in (dload_addresses | cstore_spad_addresses), (
                    f"Expected cload SPAD address {tokens[3]} to be in {dload_addresses | cstore_spad_addresses} "
                    f"in line: {", ".join(tokens)}"
                )
            elif tokens[1].startswith("ifetch"):
                # Assert ifetch target is digits
                assert tokens[2].isdigit(), f"Expected ifetch target {tokens[2]} to be digit in line: {", ".join(tokens)}"
                # Assert ifetch target is a valid xinst bundle
                assert (
                    int(tokens[2]) <= last_bundle
                ), f"Expected ifetch target {tokens[2]} to be less than or equal to last bundle {last_bundle} in line: {", ".join(tokens)}"

        # Assert last line contains cexit (termination instruction)
        last_tokens = cinstrs[-1]
        assert "cexit" in last_tokens[1], "Expected last line to contain cexit termination instruction"

        # Assert no csyncm instructions are present in cinsts
        assert not any("csyncm" in tokens[1] for tokens in cinstrs), "Expected no csyncm instructions in cinst output file for no HBM mode"
