# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file test_he_link.py
@brief Integration tests for the he_link module
"""
import tempfile
import shutil
from pathlib import Path
import pytest

import he_link
from linker.linker_run_config import LinkerRunConfig
from linker.kern_trace.trace_info import TraceInfo


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
            with open(out_file, "r", encoding="utf-8") as fout, open(
                in_file, "r", encoding="utf-8"
            ) as fin:
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
        fixtures_root = (
            Path(__file__).parent / "linking_fixtures" / fixture_dir / "no_hbm"
        )
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
        with open(out_file, "r", encoding="utf-8") as fout, open(
            input_files["xinst"], "r", encoding="utf-8"
        ) as fin:
            assert sum(1 for _ in fout) == sum(1 for _ in fin)

        # Assert no csyncm instructions in cinst output file
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.cinst"
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert (
                "csyncm" not in content
            ), "Found csyncm instruction in cinst output file"

        # Assert minst is one line
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.minst"
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
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

    def _parse_mem_file(self, mem_file):
        """
        Helper to parse mem file and return dload/dstore vars and labels.
        Also checks address uniqueness/consecutiveness and duplicates.
        """
        assert mem_file.exists()

        with open(mem_file, "r", encoding="utf-8") as f:
            split_lines = f.read().splitlines()
        dload_vars, dload_var_labels = [], set()
        dstore_vars, dstore_var_labels = [], set()
        for idx, line in enumerate(split_lines):
            tokenized_line = line.split(",")
            if line.startswith("dload"):
                var_name = tokenized_line[3].strip()
                dload_vars.append(var_name)
                if var_name.startswith("ct") or var_name.startswith("pt"):
                    dload_var_labels.add(var_name.split("_")[0])
            if line.startswith("dstore"):
                var_name = tokenized_line[1].strip()
                dstore_vars.append(var_name)
                if var_name.startswith("ct") or var_name.startswith("pt"):
                    dstore_var_labels.add(var_name.split("_")[0])
            # Assert addresses are unique and consecutive
            assert idx == int(
                tokenized_line[2]
            ), f"Expected address {idx + 1} but found {tokenized_line[2]} in line: {line}"
        assert len(dload_vars) == len(
            set(dload_vars)
        ), "Found duplicate dload variables in mem file"
        assert len(dstore_vars) == len(
            set(dstore_vars)
        ), "Found duplicate dstore variables in mem file"
        return dload_var_labels, dstore_var_labels

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_run_he_link_on_trace_file_hbm(self, temp_dir, fixture_dir):
        """
        @brief Test he_link.py with a trace file input from linking_fixtures
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
            "has_hbm": True,
            "hbm_size": 2048,
        }

        # Copy to temp input dir
        Path(cfg_kwargs["input_dir"]).mkdir(parents=True, exist_ok=True)
        shutil.copy(fixtures_root / trace_file_name, cfg_kwargs["input_dir"])

        # Copy hbm folder content to input_dir
        hbm_dir = fixtures_root / "hbm"
        for item in hbm_dir.iterdir():
            if item.is_file():
                shutil.copy(item, cfg_kwargs["input_dir"])

        # Prepare config
        Path(cfg_kwargs["output_dir"]).mkdir(exist_ok=True)

        # Run he_link
        he_link.main(LinkerRunConfig(**cfg_kwargs))

        # Check output .xinst files exist
        out_file = (
            Path(cfg_kwargs["output_dir"]) / f"{cfg_kwargs['output_prefix']}.xinst"
        )
        assert out_file.exists()

        # Extract trace vars
        kernel_ops = TraceInfo.parse_kernel_ops_from_file(cfg_kwargs["trace_file"])
        overall_input_vars, overall_output_vars, intermediate_vars = (
            self._extract_trace_vars(kernel_ops)
        )

        # Check output *.mem
        dload_var_labels, dstore_var_labels = self._parse_mem_file(
            Path(cfg_kwargs["output_dir"]) / f"{cfg_kwargs['output_prefix']}.mem"
        )

        # Assert dload and dstore vars match overall input/output trace vars
        assert dload_var_labels == overall_input_vars
        assert dstore_var_labels == overall_output_vars

        # Assert no intermediate variables in *.mem file
        assert not dload_var_labels.intersection(intermediate_vars), (
            "Found intermediate variables in dload_var_labels: "
            f"{dload_var_labels.intersection(intermediate_vars)}"
        )
        assert not dstore_var_labels.intersection(intermediate_vars), (
            "Found intermediate variables in dstore_var_labels: "
            f"{dstore_var_labels.intersection(intermediate_vars)}"
        )

    @pytest.mark.parametrize(
        "fixture_dir",
        ["bgv_multi_add_add_mul_8192_l1_m2", "bgv_multi_mul_relin_16384_l1_m2"],
    )
    def test_run_he_link_on_trace_file_no_hbm(self, temp_dir, fixture_dir):
        """
        @brief Test he_link.py with a trace file input from linking_fixtures
        """
        fixtures_root = Path(__file__).parent / "linking_fixtures" / fixture_dir
        trace_file_name = f"{fixture_dir}_program_trace.csv"
        in_trace_file = fixtures_root / trace_file_name

        # Copy to temp input dir
        input_dir = Path(temp_dir) / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(in_trace_file, input_dir)

        # Copy hbm folder content to input_dir
        hbm_dir = fixtures_root / "no_hbm"
        for item in hbm_dir.iterdir():
            if item.is_file():
                shutil.copy(item, input_dir)

        # Prepare config
        output_dir = Path(temp_dir) / "output"
        output_dir.mkdir(exist_ok=True)
        trace_file = input_dir / trace_file_name
        cfg_kwargs = {
            "input_prefixes": [],
            "output_prefix": "linked_output_trace",
            "input_mem_file": None,
            "input_dir": str(input_dir),
            "output_dir": str(output_dir),
            "trace_file": str(trace_file),
            "using_trace_file": True,
            "use_xinstfetch": False,
            "has_hbm": False,
            "hbm_size": 2048,
        }

        # Run he_link
        he_link.main(LinkerRunConfig(**cfg_kwargs))

        # Check output .xinst files exist
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.xinst"
        assert out_file.exists()

        # Assert no csyncm instructions in cinst output file
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.cinst"
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert (
                "csyncm" not in content
            ), "Found csyncm instruction in cinst output file"

        # Assert minst is one line
        out_file = output_dir / f"{cfg_kwargs['output_prefix']}.minst"
        assert out_file.exists()
        with open(out_file, "r", encoding="utf-8") as f:
            content = f.read()
            assert content.count("\n") == 1, "Expected minst output to be a single line"
